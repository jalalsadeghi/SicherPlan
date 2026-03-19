const supportedRanges = ['^20.19.0', '^22.18.0', '^24.0.0'];
const current = process.versions.node;

const [major, minor] = current.split('.').map(Number);
const supported =
  (major === 20 && minor >= 19) ||
  (major === 22 && minor >= 18) ||
  major >= 24;

if (supported) {
  process.exit(0);
}

const message = [
  '',
  `Unsupported Node.js version: ${current}`,
  `This official vue-vben-admin workspace requires Node ${supportedRanges.join(' or ')}.`,
  'Recommended local setup:',
  '  1. cd web',
  '  2. nvm use',
  '  3. pnpm install',
  '  4. pnpm dev --filter=@vben/web-antd -- --host 0.0.0.0 --port 5173',
  '',
  'This repository includes .nvmrc with 22.22.0.',
  '',
].join('\n');

console.error(message);
process.exit(1);
