Deployment Tutorial
===================

This guide explains how to deploy the desAInz platform using Docker and
Kubernetes.

.. rubric:: Prerequisites

* Docker installed on the target machine.
* Kubernetes cluster with access to required secrets.

.. rubric:: Steps

1. Build the Docker images::

    make docker-build

2. Push images to the registry::

    make docker-push

3. Apply Kubernetes manifests::

    kubectl apply -f infrastructure/k8s

After the pods start successfully, the services will be available on their
configured ports.
