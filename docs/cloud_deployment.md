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
   docker tag desainz:latest "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/desainz:latest"
   docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/desainz:latest"
   ```
2. **Create infrastructure** with Terraform.

   ```hcl
   module "desainz_ecr" {
     source = "terraform-aws-modules/ecr/aws"
     name   = "desainz"
   }

   module "desainz_ecs" {
     source          = "terraform-aws-modules/ecs/aws"
     name            = "desainz"
     container_image = module.desainz_ecr.repository_url
     cpu             = 512
     memory          = 1024
     environment     = {
       DATABASE_URL = var.database_url
       REDIS_URL    = var.redis_url
     }
     secrets = [{
       name      = "SECRET_KEY"
       value_from = aws_secretsmanager_secret.secret_key.arn
     }]
   }
   ```

3. **Store secrets** like `SECRET_KEY`, `DATABASE_URL` and `OPENAI_API_KEY` in
   AWS Secrets Manager and reference them in the ECS task definition.
4. **Expose the service** using an Application Load Balancer with TLS
   termination. Use Route 53 for DNS records.

## GCP

1. **Upload images** to Google Artifact Registry.
   ```bash
   gcloud artifacts repositories create desainz --repository-format=docker --location="$REGION"
   docker build -t gcr.io/$PROJECT_ID/desainz .
   docker push gcr.io/$PROJECT_ID/desainz
   ```
2. **Deploy** to Cloud Run or GKE using Terraform.
   ```hcl
   module "desainz_run" {
     source  = "terraform-google-modules/cloud-run/google"
     name    = "desainz"
     image   = "gcr.io/${var.project}/desainz"
     env_vars = {
       DATABASE_URL = var.database_url
       REDIS_URL    = var.redis_url
     }
     secret_env_vars = [{
       env_var = "SECRET_KEY"
       secret   = google_secret_manager_secret.secret_key.id
     }]
   }
   ```
3. **Store environment variables and API tokens** such as `SECRET_KEY` and
   `OPENAI_API_KEY` in Secret Manager and grant the Cloud Run service account
   access.
4. **Configure networking** with Cloud Run ingress and optionally set up a Cloud
   Load Balancer for custom domains and TLS certificates.

## Azure

1. **Push images** to Azure Container Registry (ACR).
   ```bash
   az acr create --name desainz --resource-group "$RESOURCE_GROUP" --sku Basic
   docker build -t desainz .
   az acr login --name desainz
   docker tag desainz:latest desainz.azurecr.io/desainz:latest
   docker push desainz.azurecr.io/desainz:latest
   ```
2. **Deploy with Terraform** to Azure Container Instances or AKS.
   ```hcl
   module "desainz_aci" {
     source              = "Azure/aci/azurerm"
     name                = "desainz"
     resource_group_name = azurerm_resource_group.main.name
     image               = "desainz.azurecr.io/desainz:latest"
     cpu                 = 1
     memory              = 2
     environment_variables = {
       DATABASE_URL = var.database_url
       REDIS_URL    = var.redis_url
     }
     secure_environment_variables = {
       SECRET_KEY      = azurerm_key_vault_secret.secret_key.value
       OPENAI_API_KEY  = azurerm_key_vault_secret.openai_key.value
     }
   }
   ```
3. **Manage secrets** like `SECRET_KEY` with Azure Key Vault and mount them using
   the CSI driver when running on AKS.
4. **Expose the service** with an Azure Application Gateway or Ingress
   Controller to provide TLS termination and custom domains.

These high-level steps give an overview of deploying the application on each cloud platform. Refer to the provider documentation for production hardening guidance.
