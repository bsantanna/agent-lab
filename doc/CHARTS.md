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

### Setup Networking

A few services in this guide are accessible via Web Browser UI, it is required to determine FQDN in advance:

- `<agent_lab_fqdn>`: a fqdn to access Agent-Lab via nginx ingress, example: *agent-lab.my-domain.com*
- `<elasticsearch_fqdn>`: a fqdn to access elasticsearch cluster via nginx ingress, example: *elasticsearch.my-domain.com*
- `<kibana_fqdn>`: a fqdn to access kibana via nginx ingress, example: *kibana.my-domain.com*
- `<vault_fqdn>`: a fqdn to access vault via nginx ingress, example: *vault.my-domain.com*

Obtain minikube vm ip address:

```bash
minikube ip
# 192.168.49.2
```

After the domain names are determined, modify system hosts file to include all these domains assigned to minikube vm ip address:
```txt

192.168.49.2 vault.my-domain.com kibana.my-domain.com elasticsearch.my-domain.com agent-lab.my-domain.com

```

### Setup Certificate Manager

To manage TLS certificates, we will use the [cert-manager](https://cert-manager.io/docs/). This tool automates the management and issuance of TLS certificates.

**Note**: If the deployment does not require a valid HTTPS certificate, this step can be skipped.

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

2. Install CNPG Operator:

```bash
helm upgrade --install cnpg --namespace cnpg-system --create-namespace cnpg/cloudnative-pg
```

3. Install PostgresSQL clusters using Helm:

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
echo "$(kubectl get secret <deployment_name>-cluster-app -o jsonpath='{.data.uri}' | base64 -d)"
```

Example:

```bash
echo "$(kubectl get secret pg-agent-lab-cluster-app -o jsonpath='{.data.uri}' | base64 -d)"
```

To access SQL console for the PostgreSQL instance, you can use the following command:

```bash
kubectl exec -it <deployment_name>-cluster-1 -- psql -U postgres
```

Example:

```bash
kubectl exec -it pg-agent-lab-vectors-cluster-1 -- psql -U postgres
```

```postgresql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Setup Vault

[Vault](https://developer.hashicorp.com/vault/docs) is used by Agent-Lab to manage secrets and sensitive data.

1. Add the HashiCorp Helm repository:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
```

2. Install Vault using Helm:

Please replace `<vault_fqdn>` with the fully qualified domain name (FQDN) you want to use for accessing Vault, example `vault.my-domain.com`.

```bash
helm install agent-lab-vault hashicorp/vault --values - <<EOF
server:
  affinity: ""
  ingress:
    enabled: true
    ingressClassName: nginx
    hosts:
      - host: "<vault_fqdn>"
        paths:
          - "/"
    tls:
      - secretName: "vault-tls-secret"
        hosts:
          - "<vault_fqdn>"
EOF
```

3. Initialize Vault cluster:

```bash
kubectl exec agent-lab-vault-0 -- vault operator init \
    -key-shares=1 \
    -key-threshold=1 \
    -format=json > cluster-keys.json
```

4. Unseal Vault cluster:

```bash
export VAULT_UNSEAL_KEY=$(jq -r ".unseal_keys_b64[]" cluster-keys.json)
kubectl exec agent-lab-vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY
```

**Note**: This is a reference implementation, in a real scenario you should use a production-ready Vault cluster, please refer to [Vault section](VAULT.md) for more details.

5. Initialize Vault Secrets Engine with Agent-Lab secrets, assuming the same domain used in the example: [https://vault.my-domain.com](https://vault.my-domain.com)


### Setup Elastic Kubernetes Cluster (ECK) for Observability

This section describes how to setup an Elastic Kubernetes Cluster (ECK) for observability purposes, including logging and monitoring, while it is not strictly necessary for running Agent-Lab, it is highly recommended to have a proper observability stack in place.

1. Add the Elastic Helm repository:

```bash
helm repo add elastic https://helm.elastic.co
helm repo update
```

2. Install the ECK operator:

```bash
helm install elastic-operator elastic/eck-operator --namespace elastic-system --create-namespace
```

3. Create the ElasticSearch cluster:

- Replace `<elasticsearch_fqdn>` with the fully qualified domain name (FQDN) you want to use for accessing ElasticSearch, example `elasticsearch.my-domain.com`.

- Replace `<kibana_fqdn>` with the fully qualified domain name (FQDN) you want to use for accessing Kibana, example `kibana.my-domain.com`.


```bash
helm install agent-lab-elastic elastic/eck-stack --namespace infra --values - <<EOF
eck-elasticsearch:
  enabled: true
  fullnameOverride: elasticsearch
  ingress:
    enabled: true
    className: nginx
    hosts:
      - host: <elasticsearch_fqdn>
        path: /
    tls:
      enabled: true
    annotations:
      kubernetes.io/ingress.class: nginx
      kubernetes.io/tls-acme: "true"
      nginx.ingress.kubernetes.io/proxy-ssl-verify: "false"
      nginx.ingress.kubernetes.io/backend-protocol: HTTPS

eck-kibana:
  enabled: true
  fullnameOverride: kibana
  config:
    xpack:
      fleet:
        packages:
          - name: apm
            version: latest
  ingress:
    enabled: true
    className: nginx
    hosts:
      - host: <kibana_fqdn>
        path: /
    tls:
      enabled: true
    annotations:
      kubernetes.io/ingress.class: nginx
      kubernetes.io/tls-acme: "true"
      nginx.ingress.kubernetes.io/proxy-ssl-verify: "false"
      nginx.ingress.kubernetes.io/backend-protocol: HTTPS

eck-apm-server:
  enabled: true
  elasticsearchRef:
    name: elasticsearch
  kibanaRef:
    name: kibana
EOF
```

---

## Deploying Agent-Lab with Helm

...

---

## Verifying the Deployment

...

---
