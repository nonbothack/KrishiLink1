import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';

const dist = join(process.cwd(), 'dist');
const forbiddenNames = [/VITE_(?:AGMARKNET|MANDI)_API_KEY/i, /VITE_WEB_PUSH_VAPID_PRIVATE_KEY/i];
const secrets = [
  'AGMARKNET_API_KEY', 'MANDI_API_KEY', 'VITE_AGMARKNET_API_KEY', 'VITE_MANDI_API_KEY',
  'WEB_PUSH_VAPID_PRIVATE_KEY', 'VITE_WEB_PUSH_VAPID_PRIVATE_KEY',
]
  .map((name) => process.env[name]?.trim())
  .filter((value) => value && value.length >= 8);

async function inspect(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await inspect(path);
      continue;
    }
    let content;
    try {
      content = await readFile(path, 'utf8');
    } catch {
      continue;
    }
    if (forbiddenNames.some((pattern) => pattern.test(content)) || secrets.some((secret) => content.includes(secret))) {
      throw new Error('Provider credential material was found in the frontend build output.');
    }
  }
}

await inspect(dist);
process.stdout.write('Frontend build contains no configured provider credential material.\n');
