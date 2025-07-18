// @flow
/**
 * Start the Next.js server with memory monitoring.
 *
 * This script runs "next start" with a maximum heap size and logs
 * memory usage every minute.
 */
import { spawn } from 'child_process';

const next = spawn(
  'node',
  ['--max-old-space-size=2048', './node_modules/.bin/next', 'start'],
  { stdio: 'inherit' }
);

setInterval(() => {
  const usage = process.memoryUsage();
  console.log(`Memory Usage - RSS: ${usage.rss}, Heap Used: ${usage.heapUsed}`);
}, 60000);

next.on('close', (code) => process.exit(code ?? 0));
