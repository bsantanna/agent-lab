<h2 align="center"><a href="https://github.com/bsantanna/agent-lab">Agent-Lab | 🤖🧪</a></h2>
<h3 align="center">Helm Charts</h3>

---

#### Table of Contents

- [Introduction](#introduction)
- [Setup Kubernetes Cluster](#setup-kubernetes-cluster)
- [Setup Dependencies](#setup-dependencies)
- [Deploy Agent-Lab](#deploy-agent-lab)

---

## Introduction

Agent-Lab provides Terraform scripts to deploy the application and its dependencies on Kubernetes clusters.

In this document, we will cover a example deployment of Agent-Lab by on Kubernetes using the provided Terraform scripts.

---

## Setup Kubernetes Cluster

### Setup for Linux Users

**Note**: In this reference documentation, a [Minikube](https://minikube.sigs.k8s.io/docs/) cluster is used, in a real scenario you should use a production-ready Kubernetes cluster.

#### Setup Kubernetes Cluster with Minikube

This section describes how to setup a Kubernetes cluster with the necessary resources for running Agent-Lab and its dependencies.

1. Minikube cluster with sufficient resources. The following command allocates 20GB of memory and 4 CPUs to the Minikube VM:

```bash
minikube start --memory=20g --cpus=4
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

---

## Setup Dependencies


#### Install Traefik Ingress with Helm Chart

```bash
cd terraform/01_traefik/
terraform init
terraform apply
```

#### Setup Networking

Modify system hosts file to include domains assigned to localhost address:
```txt

127.0.0.1 vault.my-domain.com kibana.my-domain.com elasticsearch.my-domain.com agent-lab.my-domain.com

```

### Setup Cert Manager

To manage TLS certificates, we will use the [cert-manager](https://cert-manager.io/docs/). This tool automates the management and issuance of TLS certificates.

```bash
cd terraform/02_cert-manager/
terraform init
terraform apply
```

And Create a ClusterIssuer for Let's Encrypt production:

```bash
```bash
cd terraform/03_cert-cluster-issuer/
terraform init
terraform apply
```

### Setup Redis Operator

Redis is used by Agent-Lab for pub/sub status updates for long operations.

```bash
cd terraform/04_redis-operator/
terraform init
terraform apply
```

### Setup PostgreSQL Operator

PostgreSQL is used by Agent-Lab to store relational data, vector search and dialog memory (checkpointer).
Please refer to [Entity Domain Model](DOMAIN.md) for more details about the data model.

```bash
cd terraform/05_postgres-operator/
terraform init
terraform apply
```

### Setup Keycloak

[Keycloak](https://www.keycloak.org/operator/installation#_installing_by_using_kubectl_without_operator_lifecycle_manager) is used by Agent-Lab to manage user authentication.

```bash
cd terraform/06_keycloak-operator/
terraform init
terraform apply
```

```bash
cd terraform/10_keycloak-instance/
terraform init
terraform apply
```

Please refer to [Keycloak guide](KEYCLOAK.md) for detailed steps how setting up OIDC connection.

### Setup Vault

[Vault](https://developer.hashicorp.com/vault/docs) is used by Agent-Lab to manage secrets and sensitive data.

```bash
cd terraform/08_vault-instance/
terraform init
terraform apply
```

1. Initialize Vault cluster:

```bash
kubectl --namespace vault exec vault-0 -- vault operator init \
    -key-shares=1 \
    -key-threshold=1 \
    -format=json > cluster-keys.json
```

2. Unseal Vault cluster:

```bash
export VAULT_UNSEAL_KEY=$(jq -r ".unseal_keys_b64[]" cluster-keys.json)
kubectl --namespace agent-lab exec agent-lab-vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY
```

Copy the root_token from cluster_keys.json file to a safe place, this token is used in the next step for logging in:

3. Access the `<vault_fqdn>` using web browser, assuming the same domain used in the example: [https://vault.my-domain.com](https://vault.my-domain.com)

<div align="center">

![Vault Login](vault_login.png)

</div>

4. Create a engine:

```txt
Secrets Engine > Enable new engine + > KV

For the *Path* value, use `secret`
```

5. Inside engine `secret` create a secret with path `app_secrets` and following content (replace ??? by valid values):

```json
{
  "api_base_url": "https://<agent_lab_fqdn>/",
  "auth_enabled": "True",
  "auth_url": "https://<auth_fqdn>/",
  "auth_realm": "<realm_name>",
  "auth_client_id": "<client_id>",
  "auth_client_secret": "<client_secret>",
  "broker_url": "redis://redis-agent-lab.agent-lab.svc.cluster.local:6379/0",
  "cdp_url": "http://cdp-agent-lab.agent-lab.svc.cluster.local:9222",
  "db_checkpoints": "postgresql://???:???@pg-agent-lab-checkpoints-cluster-rw.agent-lab.svc.cluster.local:5432/app",
  "db_url": "postgresql://???:???@pg-agent-lab-cluster-rw.agent-lab.svc.cluster.local:5432/app",
  "db_vectors": "postgresql://???:???@pg-agent-lab-vectors-cluster-rw.agent-lab.svc.cluster.local:5432/app",
  "tavily_api_key": "???"
}
```

**Note**: This is a reference implementation, in a real scenario you should use a production-ready Vault cluster, please refer to [Vault section](VAULT.md) for more details.

### Setup LangWatch

[LangWatch](https://langwatch.ai) is used by Agent-Lab for observability of LLM usage and simulation testing.

Please determine a <langwatch_fqdn> for accessing LangWatch web UI, example: langwatch.my-domain.com
Helm deployment Reference documentation

```bash
cd terraform/09_langwatch-instance/
terraform init
terraform apply
```

### Setup Elastic Kubernetes Cluster (ECK) for Observability

This section describes how to setup an Elastic Kubernetes Cluster (ECK) for observability purposes, including logging and monitoring, while it is not strictly necessary for running Agent-Lab, it is highly recommended to have a proper observability stack in place.

```bash
cd terraform/07_elastic-operator/
terraform init
terraform apply
```

```bash
cd terraform/11_elastic-instance/
terraform init
terraform apply
```

Use the following command to obtain `elastic` user password:

```bash
echo "$(kubectl --namespace elastic get secret elasticsearch-es-elastic-user -o=jsonpath='{.data.elastic}' | base64 --decode)"
```

Take note of APM Access Token, it is used in the next step to configure OpenTelemetry Collector.
```bash
echo "$(kubectl --namespace elastic get secret/elastic-eck-apm-server-apm-token \
    -o go-template='{{index .data "secret-token" | base64decode}}')"
```

### Setup OpenTelemetry Collector

```bash
cd terraform/12_otel-instance/
terraform init
terraform apply
```

---

## Deploy Agent-Lab

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
  LANGWATCH_ENDPOINT: "http://agent-lab-langwatch-app.agent-lab.svc.cluster.local:5560"
  LANGWATCH_API_KEY: "???"
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
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/limit-rps: "5"
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
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/limit-rps: "5"
livenessProbe:
  timeoutSeconds: 60
readinessProbe:
  timeoutSeconds: 60
image:
  tag: "v1.1.1"
EOF
```


---
