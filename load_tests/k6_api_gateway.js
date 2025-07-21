// @flow
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: __ENV.USERS ? parseInt(__ENV.USERS, 10) : 10,
  duration: __ENV.RUN_TIME || '1m',
};

const host = __ENV.GATEWAY_HOST || 'http://localhost:8080';

export default function () {
  const statusRes = http.get(`${host}/status`);
  check(statusRes, { 'status is 200': (r) => r.status === 200 });

  const optRes = http.get(`${host}/optimizations`);
  check(optRes, { 'optimizations 200': (r) => r.status === 200 });

  sleep(1);
}

export function handleSummary(data) {
  if (__ENV.RESULTS_PATH) {
    return { [__ENV.RESULTS_PATH]: JSON.stringify(data, null, 2) };
  }
  return {};
}
