// @flow

/**
 * Exit the process with a non-zero code if any warning is emitted.
 *
 * @param {Error | string} warning - The warning object or message.
 */
process.on('warning', (warning) => {
  process.stderr.write(
    `${
      typeof warning === 'string' ? warning : warning.stack || String(warning)
    }\n`
  );
  if (process.exitCode === undefined) {
    process.exitCode = 1;
  }
});
