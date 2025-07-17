/**
 * Lightweight tRPC client returning placeholder data.
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

export const trpc = {
  ping: {
    async mutate(): Promise<{ message: string; user: string }> {
      return { message: 'pong', user: 'admin' };
    },
  },
  signals: {
    async list(): Promise<Signal[]> {
      return [
        { id: 1, content: 'New trend', source: 'twitter' },
        { id: 2, content: 'Fresh design idea', source: 'reddit' },
      ];
    },
  },
  heatmap: {
    async list(): Promise<HeatmapEntry[]> {
      return [
        { label: 'cats', count: 10 },
        { label: 'dogs', count: 7 },
      ];
    },
  },
  gallery: {
    async list(): Promise<GalleryItem[]> {
      return [
        { id: 1, imageUrl: '/img/mock1.png', title: 'Mock 1' },
        { id: 2, imageUrl: '/img/mock2.png', title: 'Mock 2' },
      ];
    },
  },
  publishTasks: {
    async list(): Promise<PublishTask[]> {
      return [
        { id: 1, title: 'Cats Tee', status: 'pending' },
        { id: 2, title: 'Dogs Hoodie', status: 'scheduled' },
      ];
    },
  },
  analytics: {
    async summary(): Promise<AnalyticsData> {
      return { revenue: 1234.56, conversions: 42 };
    },
  },
};

export async function pingExample(): Promise<void> {
  const result = await trpc.ping.mutate();
  console.log(result.message, result.user);
}
