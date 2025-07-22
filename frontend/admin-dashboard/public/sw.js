// @flow

/* eslint-disable no-var */

declare var self: mixed;

self.addEventListener('message', (event: MessageEvent<mixed>): void => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
