// @flow
/**
 * Custom production server using Node's HTTP/2 module.
 *
 * This server starts Next.js with HTTP/2 support and logs memory usage
 * every minute.
 */

import { createServer, createSecureServer, type Http2Server } from 'http2';
import fs from 'fs';
import { parse } from 'url';
import next from 'next';

const port: number = parseInt(process.env.PORT ?? '3000', 10);
const dev: boolean = process.env.NODE_ENV !== 'production';

const app = next({ dev });
const handle = app.getRequestHandler();

type Options = {
  allowHTTP1: boolean,
  key?: Buffer,
  cert?: Buffer,
};

function buildOptions(): Options {
  const options: Options = { allowHTTP1: true };
  if (process.env.HTTPS_KEY_PATH && process.env.HTTPS_CERT_PATH) {
    options.key = fs.readFileSync(process.env.HTTPS_KEY_PATH);
    options.cert = fs.readFileSync(process.env.HTTPS_CERT_PATH);
  }
  return options;
}

app.prepare().then(() => {
  const options = buildOptions();
  const server: Http2Server =
    options.key && options.cert
      ? createSecureServer(options, (req, res) => {
          const parsedUrl = parse(req.url ?? '', true);
          handle(req, res, parsedUrl);
        })
      : createServer(options, (req, res) => {
          const parsedUrl = parse(req.url ?? '', true);
          handle(req, res, parsedUrl);
        });

  setInterval(() => {
    const usage = process.memoryUsage();
    // eslint-disable-next-line no-console
    console.log(`Memory Usage - RSS: ${usage.rss}, Heap Used: ${usage.heapUsed}`);
  }, 60000);

  server.listen(port, () => {
    // eslint-disable-next-line no-console
    console.log(`> Ready on ${options.key ? 'https' : 'http'}://localhost:${port}`);
  });
});
