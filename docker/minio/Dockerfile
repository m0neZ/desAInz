FROM minio/minio:latest

EXPOSE 9000

HEALTHCHECK --interval=10s --retries=5 CMD mc ready local
