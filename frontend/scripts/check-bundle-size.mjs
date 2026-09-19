import { gzipSync } from 'node:zlib';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const dist = path.resolve('dist');
const manifest = JSON.parse(readFileSync(path.join(dist, '.vite/manifest.json'), 'utf8'));
const entry = manifest['index.html'];

if (!entry?.isEntry) throw new Error('Could not find the Vite main entry in the build manifest.');

const visited = new Set();
const files = new Set();
function visit(key) {
  if (visited.has(key)) return;
  visited.add(key);
  const item = manifest[key];
  if (!item) throw new Error(`Build manifest is missing ${key}.`);
  if (item.file) files.add(item.file);
  for (const cssFile of item.css ?? []) files.add(cssFile);
  for (const importedKey of item.imports ?? []) visit(importedKey);
}
visit('index.html');

let javascriptBytes = 0;
let firstLoadBytes = 0;
for (const file of files) {
  const filePath = path.join(dist, file);
  const compressedBytes = gzipSync(readFileSync(filePath)).byteLength;
  firstLoadBytes += compressedBytes;
  if (file.endsWith('.js')) javascriptBytes += compressedBytes;
}

const javascriptLimit = 150 * 1024;
const firstLoadLimit = 400 * 1024;
console.log(`Initial JS: ${(javascriptBytes / 1024).toFixed(2)} KiB gzip / 150 KiB`);
console.log(
  `Initial JS + CSS + static assets: ${(firstLoadBytes / 1024).toFixed(2)} KiB gzip / 400 KiB`,
);

if (javascriptBytes > javascriptLimit || firstLoadBytes > firstLoadLimit) {
  throw new Error('The initial bundle exceeds the Packet 02 performance budget.');
}
