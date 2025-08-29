<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">Helm Charts</h3>

---

#### Table of Contents

- [Introduction](#introduction)
- [Setup Kubernetes Cluster](#setup-kubernetes-cluster)
- [Setup Dependencies](#setup-dependencies)
- [Agent-Lab with Helm](#deploying-agent-lab-with-helm)

---

## Introduction

Agent-Lab provides a Helm chart to deploy the application on Kubernetes clusters. This chart is designed to be flexible and customizable, allowing users to configure various aspects of the deployment.

In this document, we will cover a example deployment of Agent-Lab by on Kubernetes using the provided Helm chart.

### Preparation / Determine FQDNs

A few services in this guide are accessible via Web Browser UI, it is required to determine FQDN in advance:

- `<agent_lab_fqdn>`: a fqdn to access Agent-Lab via nginx ingress, example: *agent-lab.my-domain.com*
- `<elasticsearch_fqdn>`: a fqdn to access elasticsearch cluster via nginx ingress, example: *elasticsearch.my-domain.com*
- `<kibana_fqdn>`: a fqdn to access kibana via nginx ingress, example: *kibana.my-domain.com*
- `<vault_fqdn>`: a fqdn to access Vault via nginx ingress, example: *vault.my-domain.com*
- `<auth_fqdn>`: a fqdn to access Keycloak via nginx ingress, example: *auth.my-domain.com*


---

## Setup Kubernetes Cluster

### Setup for Linux Users

**Note**: In this reference documentation, a [Minikube](https://minikube.sigs.k8s.io/docs/) cluster is used, in a real scenario you should use a production-ready Kubernetes cluster.

#### Setup Kubernetes Cluster with Minikube

This section describes how to setup a Kubernetes cluster with the necessary resources for running Agent-Lab and its dependencies.

1. Minikube cluster with sufficient resources. The following command allocates 6GB of memory and 4 CPUs to the Minikube VM:

```bash
minikube start --memory=6g --cpus=4
```

2. Enable the Ingress addon to allow external access to the services:

```bash
minikube addons enable ingress
```

#### Setup Networking

Obtain minikube vm ip address:

```bash
minikube ip
# 192.168.49.2
```

After the domain names are determined, modify system hosts file to include domains assigned to minikube vm ip address:
```txt

192.168.49.2 vault.my-domain.com kibana.my-domain.com elasticsearch.my-domain.com agent-lab.my-domain.com

```

### Setup for Docker Desktop Users (Mac / Windows)

**Note**: In this reference documentation, a [Docker Desktop](https://docs.docker.com/desktop/features/kubernetes/) cluster is used, in a real scenario you should use a production-ready Kubernetes cluster.

#### Enable Kubernetes on Docker Desktop

<div align="center">

![Enable Kubernetes](docker_desktop_kubernetes.png)

</div>

#### Install Nginx Ingress with Helm Chart

```bash
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

#### Setup Networking

Modify system hosts file to include domains assigned to localhost address:
```txt

127.0.0.1 vault.my-domain.com kibana.my-domain.com elasticsearch.my-domain.com agent-lab.my-domain.com

```

### Create agent-lab namespace

In this guide we are going to use `agent-lab` namespace to deploy dependencies and application.

```bash
kubectl create namespace agent-lab
```

### (Optional) Setup Certificate Manager

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
  --version v1.17.4 \
  --set crds.enabled=true
```

3. Create a ClusterIssuer for Let's Encrypt prod environment:

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

---

## Setup Dependencies

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
helm install --namespace agent-lab redis-agent-lab ot-helm/redis
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

Four instances of PostgreSQL should be created, one for the Agent-Lab application, one for the vector search, one for the dialog memory (checkpointer) and one for authentication (Keycloak).

This database deployment is used for application [domain entities](DOMAIN.md):

```bash
helm upgrade --install --namespace agent-lab pg-agent-lab cnpg/cluster --values - <<EOF
cluster:
  imageName: bsantanna/cloudnative-pg-vector:17.4
  instances: 1
  storage:
    size: 1Gi
EOF
```

This database deployment is used for Vector search and RAG:

```bash
helm upgrade --install --namespace agent-lab pg-agent-lab-vectors cnpg/cluster --values - <<EOF
cluster:
  imageName: bsantanna/cloudnative-pg-vector:17.4
  instances: 1
  storage:
    size: 1Gi
EOF
```

This database deployment is used for checkpoints and storing dialog memory:

```bash
helm upgrade --install --namespace agent-lab pg-agent-lab-checkpoints cnpg/cluster --values - <<EOF
cluster:
  imageName: bsantanna/cloudnative-pg-vector:17.4
  instances: 1
  storage:
    size: 1Gi
EOF
```

This database deployment is used for authentication with Keycloak:

```bash
helm upgrade --install --namespace agent-lab pg-agent-lab-auth cnpg/cluster --values - <<EOF
cluster:
  imageName: bsantanna/cloudnative-pg-vector:17.4
  instances: 1
  storage:
    size: 1Gi
EOF
```

The connection URL for the PostgreSQL instances can be obtained using the following command:

```bash
echo "$(kubectl --namespace agent-lab get secret <deployment_name>-cluster-app -o jsonpath='{.data.uri}' | base64 -d)"
```

Example:

```bash
echo "$(kubectl --namespace agent-lab get secret pg-agent-lab-cluster-app -o jsonpath='{.data.uri}' | base64 -d)"
```

To access SQL console for the PostgreSQL instance, you can use the following command:

```bash
kubectl --namespace agent-lab exec -it <deployment_name>-cluster-1 -- psql -U postgres
```

Example:

```bash
kubectl --namespace agent-lab exec -it pg-agent-lab-vectors-cluster-1 -- psql -U postgres
```

```postgresql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Setup Keycloak

[Keycloak](https://www.keycloak.org/operator/installation#_installing_by_using_kubectl_without_operator_lifecycle_manager) is used by Agent-Lab to manage user authentication.

- Replace `<auth_fqdn>` with the fully qualified domain name (FQDN) you want to use for accessing Keycloak, example `auth.my-domain.com`.
- Replace database connection settings by the values obtained using connection url command mentioned above.
- Replace `<admin_user>` and `<admin_password>` by proper values.

```bash
helm install --namespace agent-lab kc-agent-lab oci://registry-1.docker.io/bitnamicharts/keycloak --values - <<EOF
ingress:
  enabled: true
  hostname: <auth_fqdn>
  ingressClassName: nginx
  path: /
  pathType: Prefix
  tls: true
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    kubernetes.io/ingress.class: nginx
tls:
  enabled: true
  autoGenerated: true
postgresql:
  enabled: false
externalDatabase:
  host: <db_host>
  user: <db_user>
  password: <db_password>
  database: <db_database>
  port: <db_port>
auth:
  adminUser: <admin_user>
  adminPassword: <admin_password>
EOF
```

Please refer to [Keycloak guide](KEYCLOAK.md) for detailed steps how setting up OIDC connection.


### Setup LangWatch

[LangWatch](https://langwatch.ai/) is used by Agent-Lab for observability of LLM usage.

- Please determine a <langwatch_fqdn> for accessing LangWatch web UI, example: `langwatch.my-domain.com`


```bash
helm repo add langwatch https://langwatch.github.io/langwatch/
helm repo update
```

```bash
export NEXTAUTH_SECRET=$(openssl rand -base64 32)
export API_TOKEN_JWT_SECRET=$(openssl rand -base64 32)
export CRON_API_KEY=$(openssl rand -base64 32)
echo "export NEXTAUTH_SECRET=${NEXTAUTH_SECRET}" >> langwatch_env.sh
echo "export API_TOKEN_JWT_SECRET=${API_TOKEN_JWT_SECRET}" >> langwatch_env.sh
echo "export CRON_API_KEY=${CRON_API_KEY}" >> langwatch_env.sh
```

```bash
helm --namespace agent-lab upgrade --install agent-lab-langwatch langwatch/langwatch-helm --values - <<EOF
app:
  env:
    NEXTAUTH_SECRET: ${NEXTAUTH_SECRET}
    API_TOKEN_JWT_SECRET: ${API_TOKEN_JWT_SECRET}
    BASE_HOST: https://<langwatch_fqdn>
    NEXTAUTH_URL: https://<langwatch_fqdn>
    CRON_API_KEY: ${CRON_API_KEY}
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: <langwatch_fqdn>
      paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: "agent-lab-langwatch-app"
              port:
                number: 5560
  tls:
    - secretName: langwatch-tls
      hosts:
        - <langwatch_fqdn>

EOF
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
helm --namespace agent-lab install agent-lab-vault hashicorp/vault --values - <<EOF
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
kubectl --namespace agent-lab exec agent-lab-vault-0 -- vault operator init \
    -key-shares=1 \
    -key-threshold=1 \
    -format=json > cluster-keys.json
```

4. Unseal Vault cluster:

```bash
export VAULT_UNSEAL_KEY=$(jq -r ".unseal_keys_b64[]" cluster-keys.json)
kubectl --namespace agent-lab exec agent-lab-vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY
```

Copy the root_token from cluster_keys.json file to a safe place, this token is used in the next step for logging in:

5. Access the `<vault_fqdn>` using web browser, assuming the same domain used in the example: [https://vault.my-domain.com](https://vault.my-domain.com)

<div align="center">

![Vault Login](vault_login.png)

</div>

6. Create a engine:

```txt
Secrets Engine > Enable new engine + > KV

For the *Path* value, use `secret`
```

7. Inside engine `secret` create a secret with path `app_secrets` and following content (replace ??? by valid values):

```json
{
  "api_base_url": "https://<agent_lab_fqdn>/",
  "auth_enabled": "True",
  "auth_url": "https://<auth_fqdn>/",
  "auth_realm": "<realm_name>",
  "auth_client_id": "<client_id>",
  "auth_client_secret": "<client_secret>",
  "broker_url": "redis://redis-agent-lab.agent-lab.svc.cluster.local:6379/0",
  "db_checkpoints": "postgresql://???:???@pg-agent-lab-checkpoints-cluster-rw.agent-lab.svc.cluster.local:5432/app",
  "db_url": "postgresql://???:???@pg-agent-lab-cluster-rw.agent-lab.svc.cluster.local:5432/app",
  "db_vectors": "postgresql://???:???@pg-agent-lab-vectors-cluster-rw.agent-lab.svc.cluster.local:5432/app",
  "langwatch_endpoint": "<langwatch_fqdn>",
  "langwatch_api_key": "???",
  "tavily_api_key": "???"
}
```

**Note**: This is a reference implementation, in a real scenario you should use a production-ready Vault cluster, please refer to [Vault section](VAULT.md) for more details.

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
helm --namespace agent-lab upgrade --install agent-lab-elastic elastic/eck-stack --values - <<EOF
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
      secretName: elasticsearch-tls
    annotations:
      kubernetes.io/ingress.class: nginx
      cert-manager.io/cluster-issuer: letsencrypt-prod
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
      secretName: kibana-tls
    annotations:
      kubernetes.io/ingress.class: nginx
      cert-manager.io/cluster-issuer: letsencrypt-prod
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

Use the following command to obtain `elastic` user password:

```bash
echo "$(kubectl --namespace agent-lab get secret elasticsearch-es-elastic-user -o=jsonpath='{.data.elastic}' | base64 --decode)"
```

Take note of APM Access Token, it is used in the next step to configure OpenTelemetry Collector.
```bash
echo "$(kubectl --namespace agent-lab get secret/agent-lab-elastic-eck-apm-server-apm-token \
    -o go-template='{{index .data "secret-token" | base64decode}}')"
```

### Setup OpenTelemetry Collector

1. Add OpenTelemetry Helm repository:

```bash
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
```

2. Install Otel Collector using Helm Chart:

  - Replace `<ELASTIC_APM_SECRET_TOKEN>` by the APM Access Token obtained in the last step.


```bash
helm --namespace agent-lab install agent-lab-telemetry open-telemetry/opentelemetry-collector --values - <<EOF
mode: deployment
image:
  repository: otel/opentelemetry-collector-contrib
  tag: latest
config:
  receivers:
    otlp:
      protocols:
        http:
          endpoint: "0.0.0.0:4318"
  exporters:
    otlphttp:
      endpoint: "https://agent-lab-elastic-eck-apm-server-apm-http:8200"
      headers:
        Authorization: "Bearer <ELASTIC_APM_SECRET_TOKEN>"
      tls:
        insecure_skip_verify: true
  service:
    pipelines:
      traces:
        receivers: ["otlp"]
        exporters: ["otlphttp"]
      metrics:
        receivers: ["otlp"]
        exporters: ["otlphttp"]
      logs:
        receivers: ["otlp"]
        exporters: ["otlphttp"]
EOF
```

### Verify dependencies setup

Use `kubectl --namespace agent-lab get pods` to check if all dependencies were properly installed, proceed when Running status is 1/1:

<div align="center">

![Pods for dependencies](kubectl_get_pods_dependencies.png)

</div>

---

## Deploying Agent-Lab with Helm

### Create App Secret

This Secret is used to access the Vault.

  - Replace ??? by vault `root_token` obtained in previous steps.

```bash
kubectl --namespace agent-lab apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: agent-lab-secret
type: Opaque
stringData:
  VAULT_URL: "http://agent-lab-vault.agent-lab.svc.cluster.local:8200"
  VAULT_TOKEN: "???"
EOF
```

### Install Agent-Lab with self-signed TLS certificate

  - Replace `<ollama_endpoint>` by a valid ollama endpoint in your LAN, example: `http://192.168.1.1:11434`
  - Replace `<agent_lab_fqdn>` by a valid domain name, example `agent-lab.my-domain.com`

```bash
helm --namespace agent-lab upgrade --install agent-lab agent-lab \
  --repo "https://bsantanna.github.io/agent-lab" \
  --version "1.1.1" --values - <<EOF
config:
  ollama_endpoint: "<ollama_endpoint>"
  telemetry_endpoint: "http://agent-lab-telemetry-opentelemetry-collector.default.svc.cluster.local:4318"
ingress:
  enabled: true
  hosts:
    - host: "<agent_lab_fqdn>"
      paths:
        - path: "/"
          pathType: "Prefix"
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: 50m
livenessProbe:
  timeoutSeconds: 60
readinessProbe:
  timeoutSeconds: 60
image:
  tag: "v1.1.1"
EOF
```

<div align="center">

![Deployment example](agent_lab_deployment_example.png)

</div>

### Install Agent-Lab Managed TLS certificate

#### Deploy helm chart with cert-manager cluster issuer.

  - Replace `<ollama_endpoint>` by a valid ollama endpoint in your LAN, example: `http://192.168.1.1:11434`
  - Replace `<agent_lab_fqdn>` by a valid domain name, example `agent-lab.my-domain.com`
  - Make sure the nginx ingress controller is accessible on port 80 via public internet, Cert Manager challenges are validated via HTTP.

```bash
helm --namespace agent-lab upgrade --install agent-lab agent-lab \
  --repo "https://bsantanna.github.io/agent-lab" \
  --version "1.1.1" --values - <<EOF
config:
  ollama_endpoint: "<ollama_endpoint>"
  telemetry_endpoint: "http://agent-lab-telemetry-opentelemetry-collector.default.svc.cluster.local:4318"
ingress:
  enabled: true
  hosts:
    - host: "<agent_lab_fqdn>"
      paths:
        - path: "/"
          pathType: "Prefix"
  tls:
    - hosts:
        - "<agent_lab_fqdn>"
      secretName: "agent-lab"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/proxy-body-size: 50m
livenessProbe:
  timeoutSeconds: 60
readinessProbe:
  timeoutSeconds: 60
image:
  tag: "v1.1.1"
EOF
```


---
