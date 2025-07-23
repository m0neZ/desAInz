# Kubernetes Manifests

This directory provides base Kubernetes manifests for the desAInz microservices. The files in `base/` define a generic Deployment, Service, ConfigMap, Secret and ServiceMonitor. Replace the `placeholder` names with the actual service name and adjust the image repository, tag and environment variables as required.

A `kustomization.yaml` is included so the base manifests can be deployed with Kustomize:

```bash
kubectl apply -k infrastructure/k8s/base
```

## Local Minikube

A simple overlay is provided in `overlays/minikube/` to change the Service type to `NodePort` for local testing. Apply it with:

```bash
kubectl apply -k infrastructure/k8s/overlays/minikube
```

Use `minikube service <service-name>` to access the service on your host machine.

If you have the Prometheus Operator installed in your cluster, the included
`ServiceMonitor` will scrape metrics from the service's `/metrics` endpoint.


## Blue-Green Deployments

The `overlays/blue-green` directory defines separate `blue` and `green`
Deployments for the API Gateway and the Admin Dashboard. The Service
selectors default to the `blue` version.

To switch traffic to the other color simply patch the Service selector:

```bash
# Switch API Gateway to green
kubectl patch service api-gateway -p '{"spec":{"selector":{"app":"api-gateway","color":"green"}}}'

# Switch Admin Dashboard to green
kubectl patch service admin-dashboard -p '{"spec":{"selector":{"app":"admin-dashboard","color":"green"}}}'
```

New deployments can be rolled out with `scripts/deploy.sh`, which
performs a gradual blue-green update and runs health checks.
