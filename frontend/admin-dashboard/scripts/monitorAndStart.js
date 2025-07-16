// @flow
/**
 * Start the Next.js server with memory monitoring.
 *
 * This script runs "next start" with a maximum heap size and logs
 * memory usage every minute.
 */
const { spawn } = require('child_process');

const next = spawn(
  'node',
  ['--max-old-space-size=2048', './node_modules/.bin/next', 'start'],
  { stdio: 'inherit' }
);

setInterval(() => {
  const usage = process.memoryUsage();
  // eslint-disable-next-line no-console
  console.log(
    `Memory Usage - RSS: ${usage.rss}, Heap Used: ${usage.heapUsed}`
  );
}, 60000);

next.on('close', (code) => process.exit(code ?? 0));

