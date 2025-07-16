// Periodically log memory usage to help tune Node.js runtime limits.
setInterval(() => {
  const mem = process.memoryUsage();
  console.log('Memory usage (RSS MB):', (mem.rss / 1024 / 1024).toFixed(2));
}, 60000);
