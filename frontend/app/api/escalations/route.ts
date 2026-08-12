import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import path from 'path';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const ref = searchParams.get('ref') || '';
    const status = searchParams.get('status') || '';

    const backendDir = path.resolve(process.cwd(), '..', 'backend');
    const queryScript = path.join(backendDir, 'src', 'query_api.py');

    const args = ['src/query_api.py'];
    if (ref) {
      args.push('--ref', ref);
    }
    if (status) {
      args.push('--status', status);
    }

    const { stdout } = await execFileAsync('python', args, {
      cwd: backendDir,
      encoding: 'utf-8',
      windowsHide: true,
    });

    const parsed = JSON.parse(stdout.trim() || '[]');
    return NextResponse.json({ success: true, data: parsed });
  } catch (err: any) {
    console.error('Error querying escalations API:', err);
    return NextResponse.json({ success: false, error: err?.message || 'Database query failed' }, { status: 500 });
  }
}
