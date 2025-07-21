// @flow
/**
 * Lightweight tRPC client for the dashboard.
 */
export interface Signal {
  id: number;
  content: string;
  source: string;
}

export interface HeatmapEntry {
  label: string;
  count: number;
}

export interface GalleryItem {
  id: number;
  imageUrl: string;
  title: string;
}

export interface Idea {
  id: number;
  title: string;
  status: string;
}

export interface Mockup {
  id: number;
  imageUrl: string;
  generatedAt: string;
}

export interface Metric {
  label: string;
  value: number;
}

export interface PublishTask {
  id: number;
  title: string;
  status: string;
}

export interface AnalyticsData {
  revenue: number;
  conversions: number;
}

export interface AuditLog {
  id: number;
  username: string;
  action: string;
  details: string;
  timestamp: string;
}

export interface AuditLogResponse {
  total: number;
  items: AuditLog[];
}

export interface ABTestSummary {
  ab_test_id: number;
  conversions: number;
  impressions: number;
}

export interface AppRouter {
  ping: {
    input: void;
    output: { message: string; user: string };
  };
}

const API_URL =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL ?? 'http://localhost:8000';

type Cached<Out> = { etag: string; result: Out };

const etagCache: Record<string, Cached<any>> = {};

async function call<Out, In = Record<string, unknown>>(
  procedure: string,
  input?: In
): Promise<Out> {
  const cached = etagCache[procedure];
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (cached) {
    headers['If-None-Match'] = cached.etag;
  }
  const res = await fetch(`${API_URL}/trpc/${procedure}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(input ?? {}),
    credentials: 'include',
  });
  if (res.status === 304) {
    if (!cached) {
      throw new Error('Received 304 without cached result');
    }
    return cached.result as any as Out;
  }
  if (!res.ok) {
    throw new Error(`tRPC call failed: ${res.status}`);
  }
  const etag = res.headers.get('ETag');
  const body = (await res.json()) as { result: Out };
  if (etag) {
    etagCache[procedure] = { etag, result: body.result };
  }
  return body.result;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

async function getText(path: string): Promise<string> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
  return res.text();
}

async function post(path: string, body?: unknown): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(`request failed: ${res.status}`);
  }
}

export const trpc = {
  ping: {
    mutate: () => call<{ message: string; user: string }>('ping'),
  },
  signals: {
    list: () => call<Signal[]>('signals.list'),
  },
  ideas: {
    list: () => call<Idea[]>('ideas.list'),
  },
  mockups: {
    list: () => call<Mockup[]>('mockups.list'),
  },
  heatmap: {
    list: () => call<HeatmapEntry[]>('heatmap.list'),
  },
  gallery: {
    list: () => call<GalleryItem[]>('gallery.list'),
  },
  publishTasks: {
    list: () => call<PublishTask[]>('publishTasks.list'),
  },
  approvals: {
    approve: (runId: string) => post(`/approvals/${encodeURIComponent(runId)}`),
    list: () => getJson<string[]>('/approvals'),
  },
  analytics: {
    summary: () => call<AnalyticsData>('analytics.summary'),
  },
  metrics: {
    summary: () => call<Metric[]>('metrics.summary'),
    list: () => getText('/metrics'),
  },
  auditLogs: {
    list: (limit = 50, offset = 0) =>
      getJson<AuditLogResponse>(`/audit-logs?limit=${limit}&offset=${offset}`),
  },
  optimizations: {
    list: () => getJson<string[]>('/optimizations'),
  },
  trending: {
    list: (limit = 10) => getJson<string[]>(`/trending?limit=${limit}`),
  },
  abTests: {
    summary: (id: number) => getJson<ABTestSummary>(`/ab_test_results/${id}`),
  },
};

export async function pingExample(): Promise<void> {
  const result = await trpc.ping.mutate();
  console.log(result.message, result.user);
}
