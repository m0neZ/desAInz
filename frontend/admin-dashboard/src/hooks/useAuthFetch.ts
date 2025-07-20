/* global RequestInfo, RequestInit */

export async function refreshTokens(): Promise<boolean> {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) return false;
  const res = await fetch('/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return false;
  const data = (await res.json()) as {
    access_token: string;
    refresh_token: string;
  };
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return true;
}

export async function fetchWithAuth(
  input: RequestInfo,
  init?: RequestInit
): Promise<Response> {
  const token = localStorage.getItem('token');
  const headers = new Headers(init?.headers);
  if (token) headers.set('Authorization', 'Bearer ' + token);
  const makeRequest = () => fetch(input, { ...init, headers });
  let res = await makeRequest();
  if (res.status === 401 && (await refreshTokens())) {
    headers.set(
      'Authorization',
      'Bearer ' + (localStorage.getItem('token') ?? '')
    );
    res = await makeRequest();
  }
  return res;
}
