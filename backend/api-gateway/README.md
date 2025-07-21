# API Gateway

This microservice exposes REST and tRPC-compatible endpoints and uses JWT authentication.

## Environment Variables

Copy `.env.example` to `.env` and adjust the values.

`API_GATEWAY_WS_INTERVAL_MS` controls how often metrics are pushed over
WebSocket connections.
