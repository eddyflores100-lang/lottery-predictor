/**
 * Security utilities for API routes.
 * Implements NLAB-02 (input validation), NLAB-03 (SSRF protection),
 * NLAB-08 (rate limiting), NLAB-09 (safe logging).
 */

import { NextRequest, NextResponse } from 'next/server';

// ============================================================
// NLAB-02: Input Validation — strict allowlist
// ============================================================

export const ALLOWED_LOTTERIES = new Set([
  'pozo_millonario', 'la_primitiva', 'euromillions', 'eurojackpot',
  'el_gordo', 'lotto_austrian', 'uk49s', 'sa_lotto', 'sa_powerball',
  'sa_daily_lotto', 'uk_lotto', 'irish_lotto', 'france_lotto',
  'us_powerball', 'mega_millions', 'greece_powerball', 'greek_lotto',
  'thunderball',
  // quicklotto lotteries (dynamic, but we validate prefix)
]);

export const ALLOWED_ENGINES = new Set([
  'frequency', 'hot_cold', 'gap_analysis', 'markov_chain', 'bayesian',
  'pattern_detection', 'entropy', 'monte_carlo', 'ensemble', 'lstm',
]);

/**
 * Validate lottery key — must be in allowlist OR match ql_ prefix pattern.
 * NLAB-02: No arbitrary string reaches the Python subprocess.
 */
export function validateLotteryKey(key: string): { valid: boolean; sanitized: string; error?: string } {
  if (!key || typeof key !== 'string') {
    return { valid: false, sanitized: '', error: 'Missing lottery parameter' };
  }
  // Max length to prevent DoS
  if (key.length > 64) {
    return { valid: false, sanitized: '', error: 'Lottery key too long' };
  }
  // Only allow alphanumeric, underscore, hyphen
  const sanitized = key.toLowerCase().replace(/[^a-z0-9_-]/g, '');
  if (sanitized !== key.toLowerCase()) {
    return { valid: false, sanitized: '', error: 'Invalid characters in lottery key' };
  }
  // Check allowlist or ql_ prefix
  if (ALLOWED_LOTTERIES.has(sanitized) || sanitized.startsWith('ql_')) {
    return { valid: true, sanitized };
  }
  return { valid: false, sanitized: '', error: `Unknown lottery: ${sanitized}` };
}

/**
 * Validate engine key — must be in strict allowlist.
 * NLAB-02: No arbitrary engine name reaches the subprocess.
 */
export function validateEngineKey(key: string): { valid: boolean; sanitized: string; error?: string } {
  if (!key || typeof key !== 'string') {
    return { valid: false, sanitized: '', error: 'Missing engine parameter' };
  }
  if (key.length > 32) {
    return { valid: false, sanitized: '', error: 'Engine key too long' };
  }
  const sanitized = key.toLowerCase().replace(/[^a-z_]/g, '');
  if (sanitized !== key.toLowerCase()) {
    return { valid: false, sanitized: '', error: 'Invalid characters in engine key' };
  }
  if (ALLOWED_ENGINES.has(sanitized)) {
    return { valid: true, sanitized };
  }
  return { valid: false, sanitized: '', error: `Unknown engine: ${sanitized}` };
}

// ============================================================
// NLAB-08: Rate Limiting — in-memory token bucket
// ============================================================

const RATE_LIMIT_WINDOW_MS = 60_000; // 1 minute
const RATE_LIMIT_MAX = parseInt(process.env.RATE_LIMIT_PER_MINUTE || '30', 10);
const RATE_LIMIT_BURST = parseInt(process.env.RATE_LIMIT_BURST || '10', 10);

const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

/**
 * Check rate limit for a given client IP.
 * Returns { allowed: boolean, remaining: number, resetAt: number }.
 */
export function checkRateLimit(clientIp: string): { allowed: boolean; remaining: number; resetAt: number } {
  const now = Date.now();
  const entry = rateLimitMap.get(clientIp);

  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(clientIp, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
    return { allowed: true, remaining: RATE_LIMIT_MAX - 1, resetAt: now + RATE_LIMIT_WINDOW_MS };
  }

  entry.count++;
  if (entry.count > RATE_LIMIT_MAX) {
    return { allowed: false, remaining: 0, resetAt: entry.resetAt };
  }

  return { allowed: true, remaining: RATE_LIMIT_MAX - entry.count, resetAt: entry.resetAt };
}

/**
 * Get client IP from request, handling proxies.
 */
export function getClientIp(req: NextRequest): string {
  const forwarded = req.headers.get('x-forwarded-for');
  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }
  return 'unknown';
}

/**
 * Apply rate limiting to a request. Returns null if allowed,
 * or a 429 NextResponse if rate limited.
 */
export function applyRateLimit(req: NextRequest): NextResponse | null {
  const ip = getClientIp(req);
  const { allowed, remaining, resetAt } = checkRateLimit(ip);
  
  if (!allowed) {
    const retryAfter = Math.ceil((resetAt - Date.now()) / 1000);
    return NextResponse.json(
      { error: 'Rate limit exceeded', retry_after: retryAfter },
      {
        status: 429,
        headers: {
          'Retry-After': String(retryAfter),
          'X-RateLimit-Remaining': '0',
          'X-RateLimit-Reset': String(resetAt),
        },
      }
    );
  }
  return null;
}

// ============================================================
// NLAB-09: Safe Logging — never log secrets
// ============================================================

const SECRET_PATTERNS = [
  /password/i, /secret/i, /token/i, /api_key/i, /api[-_]?key/i,
  /database_url/i, /connection_string/i, /bearer/i, /authorization/i,
  /ghp_[a-zA-Z0-9]{36}/, // GitHub tokens
  /sk-[a-zA-Z0-9]{48}/,  // OpenAI keys
];

/**
 * Sanitize a value for logging — redacts any string matching secret patterns.
 */
export function sanitizeForLogging(value: unknown): unknown {
  if (typeof value === 'string') {
    let sanitized = value;
    for (const pattern of SECRET_PATTERNS) {
      sanitized = sanitized.replace(pattern, '[REDACTED]');
    }
    // Also redact URL credentials: postgresql://user:pass@host
    sanitized = sanitized.replace(/\/\/[^:]+:[^@]+@/, '//[REDACTED]@[REDACTED]');
    return sanitized;
  }
  if (Array.isArray(value)) {
    return value.map(sanitizeForLogging);
  }
  if (value && typeof value === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value)) {
      if (SECRET_PATTERNS.some(p => p.test(key))) {
        result[key] = '[REDACTED]';
      } else {
        result[key] = sanitizeForLogging(val);
      }
    }
    return result;
  }
  return value;
}

/**
 * Safe logger that sanitizes all arguments.
 */
export function safeLog(level: 'info' | 'warn' | 'error', message: string, meta?: Record<string, unknown>) {
  const sanitizedMeta = meta ? sanitizeForLogging(meta) : undefined;
  const timestamp = new Date().toISOString();
  // NLAB-09: Never include secrets, credentials, or full URLs with auth
  const logEntry = {
    timestamp,
    level,
    message,
    ...(sanitizedMeta as Record<string, unknown>),
  };
  if (level === 'error') {
    console.error(JSON.stringify(logEntry));
  } else if (level === 'warn') {
    console.warn(JSON.stringify(logEntry));
  } else {
    console.log(JSON.stringify(logEntry));
  }
}

// ============================================================
// NLAB-03: SSRF Protection — URL validation
// ============================================================

const ALLOWED_EXTERNAL_DOMAINS = new Set([
  'bettip.co.za',
  'quicklotto.io',
  'raw.githubusercontent.com',
  'api.github.com',
  'pozomillonario.info',
  'contenidos.loteria.com.ec',
]);

const BLOCKED_IP_RANGES = [
  // Private networks — never allow fetching from these
  /^10\./,
  /^172\.(1[6-9]|2[0-9]|3[0-1])\./,
  /^192\.168\./,
  /^127\./,
  /^0\./,
  /^169\.254\./, // link-local
  /^::1$/,
  /^fc00:/,
  /^fe80:/,
];

/**
 * Validate a URL for external fetching.
 * NLAB-03: Prevents SSRF by checking domain allowlist and blocking internal IPs.
 */
export function validateExternalUrl(url: string): { valid: boolean; error?: string } {
  try {
    const parsed = new URL(url);
    
    // Only allow HTTPS
    if (parsed.protocol !== 'https:') {
      return { valid: false, error: 'Only HTTPS allowed' };
    }
    
    // Check domain allowlist
    if (!ALLOWED_EXTERNAL_DOMAINS.has(parsed.hostname)) {
      return { valid: false, error: `Domain not in allowlist: ${parsed.hostname}` };
    }
    
    // Block IP literals (prevent direct IP access to internal services)
    if (/^\d+\.\d+\.\d+\.\d+$/.test(parsed.hostname)) {
      for (const range of BLOCKED_IP_RANGES) {
        if (range.test(parsed.hostname)) {
          return { valid: false, error: 'Internal IP blocked' };
        }
      }
    }
    
    // No credentials in URL
    if (parsed.username || parsed.password) {
      return { valid: false, error: 'Credentials in URL not allowed' };
    }
    
    return { valid: true };
  } catch {
    return { valid: false, error: 'Invalid URL' };
  }
}

// ============================================================
// NLAB-02: Subprocess security — safe argument construction
// ============================================================

/**
 * Build safe subprocess arguments.
 * NLAB-02: Never pass user input directly to subprocess.
 * Uses allowlist + sanitization before constructing args.
 */
export function buildSafeSubprocessArgs(
  script: string,
  lotteryKey: string,
  engineKey: string,
): { args: string[]; error?: string } {
  // Validate all inputs
  const lotResult = validateLotteryKey(lotteryKey);
  if (!lotResult.valid) {
    return { args: [], error: lotResult.error };
  }
  
  const engResult = validateEngineKey(engineKey);
  if (!engResult.valid) {
    return { args: [], error: engResult.error };
  }
  
  // Script must be a known filename (no path traversal)
  const ALLOWED_SCRIPTS = new Set(['cli_json.py']);
  if (!ALLOWED_SCRIPTS.has(script)) {
    return { args: [], error: 'Script not allowed' };
  }
  
  return {
    args: [script, 'predict', lotResult.sanitized, engResult.sanitized],
  };
}
