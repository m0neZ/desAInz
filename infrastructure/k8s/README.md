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

