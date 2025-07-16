FROM bitnami/kafka:latest

EXPOSE 9092 9093

HEALTHCHECK --interval=10s --retries=5 CMD kafka-topics.sh --bootstrap-server localhost:9092 --list > /dev/null
