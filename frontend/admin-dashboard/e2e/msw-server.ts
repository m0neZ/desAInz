import { setupServer } from 'msw/node';
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/health', (_req, res, ctx) => res(ctx.json({ api: 'ok' }))),
  rest.get('http://localhost:8000/latency', (_req, res, ctx) =>
    res(ctx.json({ average_seconds: 3600 }))
  ),
  rest.post('http://localhost:8000/trpc/signals.list', (_req, res, ctx) =>
    res(ctx.json({ result: [{ id: 1, content: 'hello', source: 'test' }] }))
  ),
  rest.post('http://localhost:8000/trpc/gallery.list', (_req, res, ctx) =>
    res(
      ctx.json({
        result: [{ id: 1, imageUrl: '/mock.png', title: 'Mockup 1' }],
      })
    )
  ),
  rest.post('http://localhost:8000/trpc/publishTasks.list', (_req, res, ctx) =>
    res(ctx.json({ result: [] }))
  ),
];

export const server = setupServer(...handlers);
