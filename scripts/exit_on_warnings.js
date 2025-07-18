// Exit process with non-zero code if any warning is emitted
process.on('warning', (warning) => {
  console.error(warning.stack || warning);
  if (process.exitCode === undefined) {
    process.exitCode = 1;
  }
});
