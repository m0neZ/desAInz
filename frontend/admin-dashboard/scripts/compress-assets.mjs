#!/usr/bin/env node
/**
 * Compress exported static assets using gzip and Brotli.
 */
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';
import { pipeline } from 'stream';
import { createGzip, createBrotliCompress, constants } from 'zlib';

const pipe = promisify(pipeline);
const outDir = path.join(process.cwd(), 'out');

const compressFile = async (file) => {
  const gzip = createGzip({ level: 9 });
  await pipe(fs.createReadStream(file), gzip, fs.createWriteStream(`${file}.gz`));
  const brotli = createBrotliCompress({
    params: {
      [constants.BROTLI_PARAM_QUALITY]: 11,
    },
  });
  await pipe(fs.createReadStream(file), brotli, fs.createWriteStream(`${file}.br`));
};

const walk = async (dir) => {
  const entries = await fs.promises.readdir(dir, { withFileTypes: true });
  await Promise.all(
    entries.map(async (entry) => {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await walk(full);
      } else if (/\.(?:js|css|html|json|svg)$/.test(entry.name)) {
        await compressFile(full);
      }
    })
  );
};

walk(outDir).catch((err) => {
  console.error(err);
  process.exit(1);
});
