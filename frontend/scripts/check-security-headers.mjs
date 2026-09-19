import { readFileSync } from 'node:fs';

const vercel = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf8'));
const nginx = readFileSync(new URL('../nginx.conf', import.meta.url), 'utf8');
const required = new Set([
  'Content-Security-Policy',
  'Strict-Transport-Security',
  'X-Content-Type-Options',
  'Referrer-Policy',
  'Permissions-Policy',
  'X-Frame-Options',
]);
const configured = new Map(
  vercel.headers.flatMap(({ headers }) => headers.map(({ key, value }) => [key, value])),
);

for (const name of required) {
  if (!configured.has(name)) throw new Error(`Vercel is missing ${name}.`);
  if (!nginx.includes(`add_header ${name} "${configured.get(name)}" always;`)) {
    throw new Error(`Nginx is missing or differs on ${name}.`);
  }
}

const csp = configured.get('Content-Security-Policy');
for (const directive of [
  "default-src 'self'",
  "script-src 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
]) {
  if (!csp.includes(directive)) throw new Error(`CSP is missing ${directive}.`);
}

console.log(
  `Verified ${required.size} matching static security headers and baseline CSP directives.`,
);
