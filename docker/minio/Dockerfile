FROM minio/minio:latest

EXPOSE 9000

COPY LICENSES /licenses/LICENSES

HEALTHCHECK --interval=10s --retries=5 CMD mc ready local
