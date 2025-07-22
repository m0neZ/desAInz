# Recommended Resource Requests

The default Kubernetes manifests in `infrastructure/k8s/base` define CPU and memory limits for each microservice. The values below work well for small clusters and can be increased when scaling out.

| Service | CPU Request | Memory Request |
|---------|-------------|----------------|
| api-gateway | 250m | 256Mi |
| analytics | 250m | 256Mi |
| feedback-loop | 250m | 256Mi |
| marketplace-publisher | 250m | 256Mi |
| monitoring | 250m | 256Mi |
| optimization | 250m | 256Mi |
| scoring-engine | 250m | 256Mi |
| signal-ingestion | 250m | 256Mi |
| ai-mockup-generation | 250m | 256Mi |
| loki | 250m | 256Mi |

Limits are set to `500m` CPU and `512Mi` memory for all services. Horizontal Pod Autoscalers scale deployments when average CPU or memory usage exceeds 70% of the requested values.
