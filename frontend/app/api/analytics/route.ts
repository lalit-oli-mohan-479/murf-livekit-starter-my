import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const channel = searchParams.get('channel') || 'All';
    const outcome = searchParams.get('outcome') || 'All';

    const backendDir = path.resolve(process.cwd(), '..', 'backend');

    const args = ['src/query_analytics.py', '--channel', channel, '--outcome', outcome];

    const { stdout } = await execFileAsync('python', args, {
      cwd: backendDir,
      encoding: 'utf-8',
      windowsHide: true,
    });

    const parsed = JSON.parse(stdout.trim() || '{}');
    return NextResponse.json({ success: true, data: parsed });
  } catch (err: any) {
    console.error('Error querying call analytics API:', err);
    return NextResponse.json(
      { success: false, error: err?.message || 'Analytics query failed' },
      { status: 500 }
    );
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { test_type = 'success', test_channel = 'Browser', test_reason = 'None' } = body;

    const backendDir = path.resolve(process.cwd(), '..', 'backend');

    const args = [
      'src/query_analytics.py',
      '--log_test',
      '--test_type',
      test_type,
      '--test_channel',
      test_channel,
      '--test_reason',
      test_reason,
    ];

    const { stdout } = await execFileAsync('python', args, {
      cwd: backendDir,
      encoding: 'utf-8',
      windowsHide: true,
    });

    const parsed = JSON.parse(stdout.trim() || '{}');
    return NextResponse.json({ success: true, data: parsed });
  } catch (err: any) {
    console.error('Error posting test call outcome:', err);
    return NextResponse.json(
      { success: false, error: err?.message || 'Logging test call failed' },
      { status: 500 }
    );
  }
}
