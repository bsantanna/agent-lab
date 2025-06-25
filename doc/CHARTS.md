<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">Helm Charts</h3>

---

#### Table of Contents

- [Introduction](#introduction)
- [Setup Dependencies](#setup-dependencies)
- [Deploying Agent-Lab with Helm](#deploying-agent-lab-with-helm)
- [Verifying the Deployment](#verifying-the-deployment)

---

## Introduction

Agent-Lab provides a Helm chart to deploy the application on Kubernetes clusters. This chart is designed to be flexible and customizable, allowing users to configure various aspects of the deployment.

In this document, we will cover a example deployment of Agent-Lab by on Kubernetes using the provided Helm chart.

**Note**: In this reference documentation, a [Minikube](https://minikube.sigs.k8s.io/docs/) cluster is used, in a real scenario you should use a production-ready Kubernetes cluster.

--- 

## Setup Dependencies

### Setup Kubernetes Cluster with Minikube

This section describes how to setup a Kubernetes cluster with the necessary resources for running Agent-Lab and its dependencies.

1. Minikube cluster with sufficient resources. The following command allocates 6GB of memory and 4 CPUs to the Minikube VM:

```bash
minikube start --memory=6g --cpus=4
```

2. Enable the Ingress addon to allow external access to the services:

```bash
minikube addons enable ingress
```

### Setup Certificate Manager

To manage TLS certificates, we will use the [cert-manager](https://cert-manager.io/docs/). This tool automates the management and issuance of TLS certificates.

1. Add Jetstack's Helm repository:

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
```

2. Install cert-manager using Helm:

```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.17.2 \
  --set crds.enabled=true
```

3. Create a ClusterIssuer for Let's Encrypt staging environment:

Next step is creating a ClusterIssuer resource that will be used to issue certificates from Let's Encrypt. 
Please replace `<your_email_address>` with your actual email address to receive notifications about certificate expiration and issues.

```bash
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: <your_email_address>
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Setup Redis

Redis is used by Agent-Lab for pub/sub status updates for long operations. 

1. Add ot-helm's repository:

```bash
helm repo add ot-helm https://ot-container-kit.github.io/helm-charts/
helm repo update
```

2. Install Redis Operator using Helm:

```bash
helm install redis-operator ot-helm/redis-operator --namespace ot-operators --create-namespace
```

3. Create a Redis cluster:

```bash
helm install redis-agent-lab ot-helm/redis
```

### Setup PostgreSQL

PostgreSQL is used by Agent-Lab to store relational data, vector search and dialog memory (checkpointer).
Please refer to [Entity Domain Model](DOMAIN.md) for more details about the data model.

1. Add the CPNG helm repository:

```bash
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo update
```

2. Install PostgresSQL clusters using Helm:

**Note**: The `bsantanna/cloudnative-pg-vector:17.4` image is used for deployment, it is a custom image that includes the [pgvector](https://github.com/pgvector/pgvector) extension for vector search capabilities, source can be found at [this repository](https://github.com/bsantanna/docker-images/blob/main/images/servers/cloudnative-pg-vector/Dockerfile)

Three instances of PostgreSQL should be created, one for the Agent-Lab application, one for the vector search and another for the dialog memory (checkpointer).

```bash
helm upgrade --install pg-agent-lab cnpg/cluster --values - <<EOF
cluster:
  imageName: bsantanna/cloudnative-pg-vector:17.4
  instances: 1
  storage:
    size: 1Gi
EOF
```

```bash
helm upgrade --install pg-agent-lab-vectors cnpg/cluster --values - <<EOF
cluster:
  imageName: bsantanna/cloudnative-pg-vector:17.4
  instances: 1
  storage:
    size: 1Gi
EOF
```

```bash
helm upgrade --install pg-agent-lab-checkpoints cnpg/cluster --values - <<EOF
cluster:
  imageName: bsantanna/cloudnative-pg-vector:17.4
  instances: 1
  storage:
    size: 1Gi
EOF
```

The connection URL for the PostgreSQL instances can be obtained using the following command:

```bash
echo "$(kubectl get secret <deployment_name> -o jsonpath='{.data.uri}' | base64 -d)"
```

Example:

```bash
echo "$(kubectl get secret pg-agent-lab -o jsonpath='{.data.uri}' | base64 -d)"
```

--- 

## Deploying Agent-Lab with Helm

...

---

## Verifying the Deployment

...

---
