import { NextResponse } from 'next/server';
import { spawn } from 'child_process';

export const dynamic = 'force-dynamic';

const PREDICTOR_DIR = '/home/z/my-project/scripts/lottery_predictor';

function runPython(script: string, args: string[] = []): Promise<{stdout: string; stderr: string; code: number}> {
  return new Promise((resolve) => {
    const proc = spawn('python3', [script, ...args], {
      cwd: PREDICTOR_DIR,
      env: { ...process.env, TF_CPP_MIN_LOG_LEVEL: '3', TF_ENABLE_ONEDNN_OPTS: '0' },
    });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });
    proc.on('close', (code) => resolve({ stdout, stderr, code: code || 0 }));
  });
}

export async function GET() {
  const result = await runPython('cli_json.py', ['lotteries']);
  try {
    const data = JSON.parse(result.stdout);
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: 'Failed to parse lotteries', stderr: result.stderr.slice(-500) }, { status: 500 });
  }
}
