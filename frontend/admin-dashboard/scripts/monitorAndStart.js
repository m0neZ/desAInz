// @flow
/**
 * Start the Next.js server with memory monitoring.
 *
 * This script runs the custom HTTP/2 server with a maximum heap size and logs
 * memory usage every minute.
 */
import { spawn } from 'child_process';

// Type annotation for the spawned Next.js process
/** @type {import('child_process').ChildProcess} */
const next = spawn('node', ['--max-old-space-size=2048', './server.js'], {
  stdio: 'inherit',
});

setInterval((): void => {
  /** @type {NodeJS.MemoryUsage} */
  const usage = process.memoryUsage();
  process.stdout.write(
    `Memory Usage - RSS: ${usage.rss}, Heap Used: ${usage.heapUsed}\n`
  );
}, 60000);

next.on('close', (code) => process.exit(code ?? 0));
