# Deployment Guide

This guide explains how to run desAInz locally with Docker Compose, deploy it to Kubernetes, and push containers to AWS, GCP and Azure. All services rely on the environment variables listed in [configuration](configuration.md). Sample values are available under `.env.dev.example`, `.env.staging.example` and `.env.prod.example`.

## Prerequisites

* Docker Engine with the Buildx plugin installed
* QEMU emulation binaries for cross-platform builds
* `docker buildx` configured as the default builder

## Docker Compose

1. Create a `.env` file by copying the appropriate example file and adjusting the values.
2. Start the stack:

   ```bash
   docker-compose up -d
   ```
3. Register schemas once all containers are healthy:

   ```bash
   python scripts/register_schemas.py
   ```
4. Initialize the object storage bucket used by the services:

   ```bash
   scripts/setup_storage.sh desainz-bucket --minio  # omit --minio for AWS S3
   ```

5. Secrets can be stored in files under `secrets/` and referenced as Docker secrets. The services read them from `/run/secrets`.

## Kubernetes

1. Base manifests live in `infrastructure/k8s`. Apply them to a cluster:

   ```bash
   kubectl apply -k infrastructure/k8s/base
   ```
2. Provide environment variables via ConfigMaps and mount sensitive values using Kubernetes Secrets. The applications automatically load secrets from `/run/secrets`. A starting template is available at `infrastructure/k8s/examples/secrets.yaml`.

   Create the secret using Helm:

   ```bash
   helm upgrade --install shared-secret infrastructure/k8s/examples \
     -f infrastructure/k8s/examples/secrets.yaml
   ```
3. Configure ingress and TLS termination for external access. An ingress controller such as NGINX is recommended.
4. Deploy individual services using the Helm charts in `infrastructure/helm`. Each chart exposes
   values for the container image tag, environment variables and optional horizontal pod
   autoscaler settings. The following commands show how to install every service with
   the provided values files:

   ```bash
   helm install signal-ingestion infrastructure/helm/signal-ingestion \
     -f infrastructure/helm/signal-ingestion/values-dev.yaml
   helm install data-storage infrastructure/helm/data-storage \
     -f infrastructure/helm/data-storage/values-dev.yaml
   helm install scoring-engine infrastructure/helm/scoring-engine \
     -f infrastructure/helm/scoring-engine/values-dev.yaml
   helm install ai-mockup-generation infrastructure/helm/ai-mockup-generation \
     -f infrastructure/helm/ai-mockup-generation/values-dev.yaml
   helm install marketplace-publisher infrastructure/helm/marketplace-publisher \
     -f infrastructure/helm/marketplace-publisher/values-dev.yaml
   helm install feedback-loop infrastructure/helm/feedback-loop \
     -f infrastructure/helm/feedback-loop/values-dev.yaml
   helm install orchestrator infrastructure/helm/orchestrator \
     -f infrastructure/helm/orchestrator/values-dev.yaml
   helm install backup-jobs infrastructure/helm/backup-jobs \
     -f infrastructure/helm/backup-jobs/values-dev.yaml
   helm install logrotate-jobs infrastructure/helm/logrotate-jobs \
     -f infrastructure/helm/logrotate-jobs/values-dev.yaml
   helm install monitoring infrastructure/helm/monitoring \
     -f infrastructure/helm/monitoring/values.yaml
   ```

   Production deployments use the corresponding `values-production.yaml` files under
   each chart directory.

   The `ai-mockup-generation` chart uses the `gpu_queue_length` metric to scale GPU
   workers. Set `hpa.enabled` to `true` and configure `hpa.gpuQueueAverageValue` in
   `values.yaml` to enable automatic scaling based on pending tasks.

5. Schedule GPU workloads by assigning the `gpu` node pool using a `nodeSelector` and
   `tolerations`. Enable GPU limits in the chart values:

   ```yaml
   resources:
     limits:
       nvidia.com/gpu: 1
   nodeSelector:
     node-type: gpu
   tolerations:
     - key: nvidia.com/gpu
       operator: Exists
       effect: NoSchedule
   ```

6. Persistent volumes are required for the `data-storage` and `backup-jobs` charts.
   Set `persistence.enabled` to `true` and specify a `storageClassName` in the values
   file to provision a volume:

   ```yaml
   persistence:
     enabled: true
     storageClassName: standard
     size: 20Gi
   ```

## Cloud Providers

See the [Cloud Provider Strategy](blueprints/DesignIdeaEngineCompleteBlueprint.md)
section of the project blueprint for recommendations on multi-cloud deployments.

### AWS

1. Build and push images to Amazon ECR:

   ```bash
   aws ecr create-repository --repository-name desainz
   ./scripts/build-images.sh
   docker tag desainz:latest <account>.dkr.ecr.<region>.amazonaws.com/desainz:latest
   docker push <account>.dkr.ecr.<region>.amazonaws.com/desainz:latest
   ```
2. Deploy using ECS or EKS. Mount secrets from AWS Secrets Manager as environment variables or files.

### GCP

1. Push images to Artifact Registry:

   ```bash
   gcloud artifacts repositories create desainz --repository-format=docker --location=<region>
   ./scripts/build-images.sh
   docker push gcr.io/<project>/desainz
   ```
2. Deploy to Cloud Run or GKE. Use GCP Secret Manager to supply sensitive values.

### Azure

1. Publish images to Azure Container Registry:

   ```bash
   az acr create --name desainz --resource-group <rg> --sku Basic
   ./scripts/build-images.sh
   az acr login --name desainz
   docker tag desainz:latest desainz.azurecr.io/desainz:latest
   docker push desainz.azurecr.io/desainz:latest
   ```
2. Run containers in Azure Container Instances or AKS. Mount secrets from Azure Key Vault using CSI drivers.

All deployments share the same environment variables. Ensure that values for credentials, API keys and connection strings are stored securely using the secret management solution of your platform.

## Rollback

Blue/green deployments update services by switching the `color` selector of the
Kubernetes `Service`. If an issue is detected after a rollout, direct traffic
back to the previous version by patching the service to the old color. Retrieve
the current color with:

```bash
kubectl get svc <service> -n <namespace> -o jsonpath='{.spec.selector.color}'
```

Then patch the selector to the desired color:

```bash
kubectl patch svc <service> -n <namespace> \
  -p '{"spec":{"selector":{"app":"<service>","color":"<previous_color>"}}}'
```

Alternatively, redeploy the desired tag using the `deploy.sh` helper which will
update the service selector and scale down the newer deployment:

```bash
./scripts/deploy.sh <service> example/<service>:<tag> <namespace>
```
