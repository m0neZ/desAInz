// @flow

/**
 * Exit the process with a non-zero code if any warning is emitted.
 *
 * @param {Error | string} warning - The warning object or message.
 */
process.on('warning', (warning: Error | string): void => {
  console.error(
    typeof warning === 'string' ? warning : warning.stack || String(warning)
  );
  if (process.exitCode === undefined) {
    process.exitCode = 1;
  }
});
