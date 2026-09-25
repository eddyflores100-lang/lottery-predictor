import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';

export const dynamic = 'force-dynamic';
export const maxDuration = 300; // 5 minutes - LSTM can take 30+s

const PREDICTOR_DIR = '/home/z/my-project/scripts/lottery_predictor';

function runPython(script: string, args: string[] = []): Promise<{stdout: string; stderr: string; code: number}> {
  return new Promise((resolve) => {
    const proc = spawn('python3', [script, ...args], {
      cwd: PREDICTOR_DIR,
      env: { ...process.env, TF_CPP_MIN_LOG_LEVEL: '3', TF_ENABLE_ONEDNN_OPTS: '0', GLOG_minloglevel: '3' },
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    let timeout: NodeJS.Timeout;
    
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });
    
    // Set 4-minute timeout
    timeout = setTimeout(() => {
      proc.kill('SIGTERM');
      resolve({ stdout, stderr: stderr + '\n[TIMEOUT after 240s]', code: -1 });
    }, 240000);
    
    proc.on('close', (code) => {
      clearTimeout(timeout);
      resolve({ stdout, stderr, code: code || 0 });
    });
    proc.on('error', (err) => {
      clearTimeout(timeout);
      resolve({ stdout, stderr: stderr + '\n[ERROR: ' + err.message + ']', code: -1 });
    });
  });
}

export async function GET(req: NextRequest) {
  const lottery = req.nextUrl.searchParams.get('lottery');
  const engine = req.nextUrl.searchParams.get('engine');

  if (!lottery || !engine) {
    return NextResponse.json({ error: 'Missing lottery or engine parameter' }, { status: 400 });
  }

  const result = await runPython('cli_json.py', ['predict', lottery, engine]);
  
  if (!result.stdout) {
    return NextResponse.json({ 
      error: 'No output from predictor', 
      stderr: result.stderr.slice(-500),
      code: result.code 
    }, { status: 500 });
  }
  
  try {
    const data = JSON.parse(result.stdout);
    if (data.error) {
      return NextResponse.json(data, { status: 500 });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ 
      error: 'Failed to parse prediction', 
      stdout_tail: result.stdout.slice(-500),
      stderr: result.stderr.slice(-500) 
    }, { status: 500 });
  }
}
