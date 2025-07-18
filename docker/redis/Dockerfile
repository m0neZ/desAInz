FROM redis:7-alpine

EXPOSE 6379

COPY LICENSES /licenses/LICENSES

HEALTHCHECK --interval=10s --retries=5 CMD redis-cli ping | grep PONG
