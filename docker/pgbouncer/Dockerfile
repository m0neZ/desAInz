FROM pgbouncer/pgbouncer:latest
COPY pgbouncer.ini /etc/pgbouncer/
EXPOSE 6432
HEALTHCHECK --interval=10s --retries=5 CMD pgbouncer --version
