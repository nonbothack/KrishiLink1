import { spawn } from 'node:child_process';
import path from 'node:path';

const url = 'http://127.0.0.1:4173';
let server;

async function isReady() {
  try {
    const response = await fetch(url);
    return response.ok;
  } catch {
    return false;
  }
}

async function waitForServer() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    if (await isReady()) return;
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error('Vite did not start within 20 seconds.');
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: process.cwd(), stdio: 'inherit', windowsHide: true });
    child.once('error', reject);
    child.once('exit', code => resolve(code ?? 1));
  });
}

try {
  if (!(await isReady())) {
    server = spawn(process.execPath, [path.resolve('node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', '4173'], {
      cwd: process.cwd(),
      stdio: 'ignore',
      windowsHide: true,
    });
    await waitForServer();
  }
  process.exitCode = await run(process.execPath, [path.resolve('node_modules/@playwright/test/cli.js'), 'test', '--workers=1']);
} finally {
  if (server) {
    server.kill();
    server.unref();
  }
}
