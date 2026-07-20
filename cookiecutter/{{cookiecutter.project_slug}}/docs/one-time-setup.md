# One-Time Cluster Setup

Bootstraps the AKS + GitOps stack under `terraform/aks/`. Everything runtime is
reconciled from git by Flux; the only manual interventions are applying the three
Terraform stages in order and creating DNS records once the load balancer exists.

Apply order: `01_aks` -> `02_gitops` -> **DNS** -> `03_vault_config`.

## Prerequisites

- `az` CLI logged in to the target subscription (`az login`), plus `kubectl`,
  `jq`, and `curl` on the machine running Terraform.
- Two GitHub PATs:
  - fine-grained, read-only **Contents** on this repo (Flux git sync, `02_gitops`);
  - classic/fine-grained with **read:packages** for pulling the private GHCR
    image (`03_vault_config` creates the `ghcr-pull` secret).
- Environment values supplied via an untracked `<env>.tfvars` file (never
  committed) or `TF_VAR_*` env vars. Secrets (`github_pat`{% if cookiecutter.auth_enabled %},
  `auth_client_secret`{% endif %}) must not be committed.

## 1. Provision the cluster (`terraform/aks/01_aks`)

Creates the AKS cluster and the Key Vault used for Vault auto-unseal and for
storing the Vault root token.

```bash
cd terraform/aks/01_aks
terraform init
terraform apply -var-file=<env>.tfvars
```

Required tfvars without defaults: `subscription_id`, `location`.

This stage is idempotent across cluster recreations. Azure Key Vault soft-deletes
rather than removes the unseal vault, so a prior cluster torn down by deleting its
resource group (or by losing Terraform state) leaves the vault — and its active
`vault-unseal` key — behind, which previously broke the key create with an
"already exists" error. The provider is configured to purge (not soft-delete) on
`terraform destroy`, and a pre-create step purges any soft-deleted remnant of the
vault name before recreating it, so every `apply` starts from a clean slate with
no manual Key Vault steps. Recreating the cluster mints a fresh unseal key and a
fresh `vault-init` payload; Vault is re-initialized cleanly by `03_vault_config`.

Configure `kubectl` for the cluster (used by the DNS lookup and verify steps):

```bash
terraform -chdir=terraform/aks/01_aks output -raw get_credentials_command | sh
```

## 2. Install Flux + GitOps sync (`terraform/aks/02_gitops`)

Deploys the Flux extension and configuration; Flux then reconciles traefik,
cert-manager, CNPG, Redis, Vault, Postgres, and the app from `gitops/`.

```bash
cd terraform/aks/02_gitops
terraform init
terraform apply -var-file=<env>.tfvars
```

Required tfvars without defaults: `subscription_id`, `github_pat` (Contents
read), `cert_manager_email`, `vault_hostname`, `app_hostname` (plus any name
overrides matching the `01_aks` apply).

Reconciliation is asynchronous and continues after `apply` returns. The private
app image stays in `ImagePullBackOff` until `03_vault_config` creates the pull
secret — expected at this stage.

## 3. DNS records

Once traefik has a LoadBalancer IP, read it:

```bash
terraform -chdir=terraform/aks/02_gitops output -raw get_traefik_ip_command | sh
```

Create an `A` record pointing **each** hostname at that IP:

- `vault_hostname -> <IP>`
- `app_hostname   -> <IP>`

cert-manager completes the HTTP-01 challenge and issues Let's Encrypt
certificates automatically once the records resolve. DNS must be in place before
the next stage, which reaches Vault over its hostname.

## 4. Initialize and configure Vault (`terraform/aks/03_vault_config`)

A single apply that bootstraps and configures everything in dependency order:

1. Waits for the Vault endpoint, runs `operator init` over the public ingress,
   and stores the root token + recovery keys in the Key Vault (secret
   `vault-init`). Auto-unseal (the azurekeyvault seal) handles every restart
   afterward, so there is no manual unseal step. Idempotent — an
   already-initialized Vault is left untouched.
2. Reads that root token back and waits for the CNPG secrets to converge.
3. Creates the `ghcr-pull` image pull secret, the Vault KV secret, and the
   Kubernetes auth role the app logs in with. Once the pull secret exists the
   app pulls its image and comes up, loading all config from Vault KV
   (`secret/app_secrets`) via agent_lab's `KubernetesVaultConfigSource`.

Vault starts sealed and uninitialized until step 1 runs. Its readiness probe
tolerates the uninitialized state (returns 204 for `uninitcode`), so the pod is
Ready and reachable through the traefik ingress before init — this is what lets
`operator init` run over the public hostname. Auto-unseal keeps it Ready across
restarts afterward; an initialized-but-sealed Vault (e.g. an auto-unseal
failure) still reports NotReady.

```bash
cd terraform/aks/03_vault_config
terraform init
terraform apply -var-file=<env>.tfvars
```

Required tfvars without defaults: `subscription_id`, `github_pat`
(read:packages), `vault_hostname`, `app_hostname`{% if cookiecutter.auth_enabled %}, `auth_url`,
`auth_client_secret` (`auth_realm` and `auth_client_id` default to
`{{ cookiecutter.project_slug }}`){% endif %}.

To retrieve the root token later for manual `vault` CLI access:

```bash
terraform -chdir=terraform/aks/03_vault_config output -raw get_root_token_command | sh
```

## Verify

```bash
az k8s-configuration flux show --resource-group rg-{{ cookiecutter.project_slug }} \
  --cluster-name aks-{{ cookiecutter.project_slug }} --cluster-type managedClusters \
  --name {{ cookiecutter.project_slug }}

kubectl get kustomizations -n flux-system      # all Ready
kubectl get helmreleases -A                    # all Ready
kubectl get clusters.postgresql.cnpg.io -n {{ cookiecutter.project_slug }}
kubectl get pods -n {{ cookiecutter.project_slug }}   # app + cdp Running
```
