const pidusage = require('pidusage');
const { spawn } = require('child_process');

const server = spawn('next', ['start'], { stdio: 'inherit' });

setInterval(() => {
  pidusage(server.pid, (err, stats) => {
    if (!err && stats) {
      const mb = Math.round(stats.memory / 1024 / 1024);
      console.log(`Next.js memory usage: ${mb} MB`);
    }
  });
}, 10000);
