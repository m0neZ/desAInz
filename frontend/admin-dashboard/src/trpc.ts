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

async function call<Out, In = Record<string, unknown>>(
  procedure: string,
  input?: In
): Promise<Out> {
  const res = await fetch(`${API_URL}/trpc/${procedure}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input ?? {}),
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`tRPC call failed: ${res.status}`);
  }
  const body = (await res.json()) as { result: Out };
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
    list: (page = 1, limit = 20) =>
      call<Signal[]>('signals.list', { page, limit }),
  },
  ideas: {
    list: () => call<Idea[]>('ideas.list'),
  },
  mockups: {
    list: (page = 1, limit = 20) =>
      call<Mockup[]>('mockups.list', { page, limit }),
  },
  heatmap: {
    list: () => call<HeatmapEntry[]>('heatmap.list'),
  },
  gallery: {
    list: (page = 1, limit = 20) =>
      call<GalleryItem[]>('gallery.list', { page, limit }),
  },
  publishTasks: {
    list: (page = 1, limit = 20) =>
      call<PublishTask[]>('publishTasks.list', { page, limit }),
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
  recommendations: {
    list: () => getJson<string[]>('/recommendations'),
  },
  auditLogs: {
    list: (page = 1, limit = 50) =>
      getJson<AuditLogResponse>(`/audit-logs?page=${page}&limit=${limit}`),
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
  process.stdout.write(`${result.message} ${result.user}\n`);
}
