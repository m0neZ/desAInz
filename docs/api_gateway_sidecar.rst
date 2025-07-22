API Gateway Nginx Sidecar
=========================

To minimize load on the API Gateway, an Nginx sidecar container is configured to cache
successful GET responses. The sidecar listens on port ``8000`` and proxies requests to
the ``api-gateway`` service. Cached responses are served directly by Nginx and include
the ``X-Cache-Status`` header.

The configuration is defined in ``docker/api_gateway_sidecar/nginx.conf`` and mounted via
``docker-compose.dev.yml``.
