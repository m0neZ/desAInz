# Cloud Deployment Guides

This document outlines how to deploy desAInz to AWS, Google Cloud Platform and Microsoft Azure using container images.

## Kubernetes

The repository ships with Kustomize manifests under `infrastructure/k8s`. Apply
the base configuration to any cluster with:

```bash
kubectl apply -k infrastructure/k8s/base
```

For local testing with Minikube use the overlay which exposes each service via
`NodePort`:

```bash
kubectl apply -k infrastructure/k8s/overlays/minikube
```

Check that all Pods are running and inspect logs using `kubectl get pods` and
`kubectl logs`.

## AWS

1. **Build and push images** to Amazon Elastic Container Registry (ECR).
   ```bash
   aws ecr create-repository --repository-name desainz
   docker build -t desainz .
   docker tag desainz:latest <account>.dkr.ecr.<region>.amazonaws.com/desainz:latest
   docker push <account>.dkr.ecr.<region>.amazonaws.com/desainz:latest
   ```
2. **Provision a cluster** using ECS or EKS.
3. **Create task definitions or Kubernetes manifests** pointing to the pushed image.
4. **Expose services** with an Application Load Balancer and configure TLS.

## GCP

1. **Upload images** to Google Artifact Registry.
   ```bash
   gcloud artifacts repositories create desainz --repository-format=docker --location=<region>
   docker build -t gcr.io/<project>/desainz .
   docker push gcr.io/<project>/desainz
   ```
2. **Deploy** to Cloud Run or GKE using the uploaded image.
3. **Configure networking and TLS** via Cloud Load Balancing.

## Azure

1. **Push images** to Azure Container Registry (ACR).
   ```bash
   az acr create --name desainz --resource-group <rg> --sku Basic
   docker build -t desainz .
   az acr login --name desainz
   docker tag desainz:latest desainz.azurecr.io/desainz:latest
   docker push desainz.azurecr.io/desainz:latest
   ```
2. **Run containers** using Azure Container Instances or AKS.
3. **Create an ingress controller** if using AKS and configure TLS.

These high-level steps give an overview of deploying the application on each cloud platform. Refer to the provider documentation for production hardening guidance.

