import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import { applyRateLimit, validateLotteryKey, validateEngineKey, buildSafeSubprocessArgs, safeLog } from '@/lib/security';

export const dynamic = 'force-dynamic';
export const maxDuration = 300;

const PREDICTOR_DIR = '/home/z/my-project/scripts/lottery_predictor';

function runPython(script: string, args: string[]): Promise<{stdout: string; stderr: string; code: number}> {
  return new Promise((resolve) => {
    // NLAB-05/08: Worker isolation — timeout, limited env, no shell
    const WORKER_TIMEOUT = parseInt(process.env.WORKER_TIMEOUT_SECONDS || '60', 10) * 1000;
    
    const proc = spawn('python3', [script, ...args], {
      cwd: PREDICTOR_DIR,
      env: {
        // NLAB-05: Minimal environment — no inherited secrets
        PATH: process.env.PATH,
        HOME: process.env.HOME,
        TF_CPP_MIN_LOG_LEVEL: '3',
        TF_ENABLE_ONEDNN_OPTS: '0',
        GLOG_minloglevel: '3',
      },
      stdio: ['pipe', 'pipe', 'pipe'],
      // NLAB-05: No shell — prevents shell injection
      shell: false,
    });
    
    let stdout = '';
    let stderr = '';
    let timeout: NodeJS.Timeout;
    
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });
    
    // NLAB-08: Enforce timeout
    timeout = setTimeout(() => {
      proc.kill('SIGTERM');
      resolve({ stdout, stderr: stderr + '\n[TIMEOUT]', code: -1 });
    }, WORKER_TIMEOUT);
    
    proc.on('close', (code) => {
      clearTimeout(timeout);
      resolve({ stdout, stderr, code: code || 0 });
    });
    proc.on('error', (err) => {
      clearTimeout(timeout);
      // NLAB-09: Safe logging — no sensitive data in error message
      safeLog('error', 'Subprocess error', { error_type: err.name });
      resolve({ stdout, stderr: '[ERROR]', code: -1 });
    });
  });
}

export async function GET(req: NextRequest) {
  // NLAB-08: Rate limiting
  const rateLimited = applyRateLimit(req);
  if (rateLimited) return rateLimited;
  
  // NLAB-02: Input validation — strict allowlist
  const rawLottery = req.nextUrl.searchParams.get('lottery') || '';
  const rawEngine = req.nextUrl.searchParams.get('engine') || 'ensemble';
  
  const lotResult = validateLotteryKey(rawLottery);
  if (!lotResult.valid) {
    safeLog('warn', 'Invalid lottery key rejected', { key_length: rawLottery.length });
    return NextResponse.json({ error: lotResult.error }, { status: 400 });
  }
  
  const engResult = validateEngineKey(rawEngine);
  if (!engResult.valid) {
    safeLog('warn', 'Invalid engine key rejected', { key_length: rawEngine.length });
    return NextResponse.json({ error: engResult.error }, { status: 400 });
  }
  
  // NLAB-02: Build safe subprocess args (no user input directly)
  const { args, error: argsError } = buildSafeSubprocessArgs('cli_json.py', lotResult.sanitized, engResult.sanitized);
  if (argsError) {
    return NextResponse.json({ error: argsError }, { status: 400 });
  }
  
  const result = await runPython('cli_json.py', args);
  
  if (!result.stdout) {
    safeLog('error', 'No output from predictor', { code: result.code });
    return NextResponse.json({ error: 'No output from predictor' }, { status: 500 });
  }
  
  try {
    const data = JSON.parse(result.stdout);
    if (data.error) {
      return NextResponse.json(data, { status: 500 });
    }
    return NextResponse.json(data);
  } catch {
    // NLAB-09: Don't expose raw stdout/stderr (may contain secrets or internal paths)
    safeLog('error', 'Failed to parse prediction output');
    return NextResponse.json({ error: 'Failed to parse prediction' }, { status: 500 });
  }
}
