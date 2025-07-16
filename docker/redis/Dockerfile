FROM redis:7-alpine

EXPOSE 6379

HEALTHCHECK --interval=10s --retries=5 CMD redis-cli ping | grep PONG
