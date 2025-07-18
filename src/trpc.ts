/**
 * Lightweight tRPC client that forwards requests to the API Gateway.
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
  analytics: {
    summary: () => call<AnalyticsData>('analytics.summary'),
  },
  metrics: {
    summary: () => call<Metric[]>('metrics.summary'),
  },
};

export async function pingExample(): Promise<void> {
  const result = await trpc.ping.mutate();
  console.log(result.message, result.user);
}
