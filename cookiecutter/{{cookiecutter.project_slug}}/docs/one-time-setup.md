# One-Time Cluster Setup

Out-of-band steps required once per environment when bootstrapping the AKS +
GitOps stack under `terraform/aks/`. Everything else is reconciled from git by
Flux; the steps below are the only manual interventions.

## 1. Provision the cluster (`terraform/aks/01_aks`)

Runs on the node holding Terraform state. Environment-specific values are
supplied via an untracked tfvars file, never committed.

```bash
cd terraform/aks/01_aks
terraform init
terraform apply -var-file=<env>.tfvars
```

Required tfvars without defaults: `subscription_id`, `location`.

## 2. Install Flux + GitOps sync (`terraform/aks/02_gitops`)

Prerequisites:

- The `gitops/` directory is present on the branch Flux tracks (`main`).
- A fine-grained GitHub PAT with read-only **Contents** access to this
  repository (git sync auth).

```bash
cd terraform/aks/02_gitops
terraform init
terraform apply -var-file=<env>.tfvars
```

Required tfvars without defaults: `subscription_id`, `github_pat`,
`cert_manager_email`, `vault_hostname` (plus any name overrides matching the
01_aks apply).

Provisioning waits for the first successful sync; the `infra-controllers` and
`infra-configs` layers must turn healthy before the `apps` layer applies.

## 3. DNS record for Vault

After traefik is up, point the Vault hostname (the `vault_hostname` tfvar) at
the traefik load balancer's public IP:

```bash
kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

Create an `A` record `<vault_hostname> -> <that IP>`. cert-manager then
completes the HTTP-01 challenge and issues the Let's Encrypt certificate.

## 4. Initialize Vault

Vault starts sealed and reports NotReady until initialized — this is expected.

```bash
kubectl exec -n vault vault-0 -- vault operator init
```

Store the recovery keys and root token securely (not in this repository). The
azurekeyvault seal provisioned by `01_aks` auto-unseals Vault on every restart
after initialization — no manual unsealing needed.

## 5. Configure Vault and app secrets (`terraform/aks/03_vault_config`)

Provisions the KV mount, the read policy, the Kubernetes auth role the app
logs in with, the GHCR image pull secret, and the `app_secrets` payload read
by agent_lab's `KubernetesVaultConfigSource` at startup.

```bash
cd terraform/aks/03_vault_config
terraform init
terraform apply -var-file=<env>.tfvars
```

Required tfvars without defaults: `subscription_id`, `vault_hostname`,
`vault_token` (the root token from step 4, or an admin token derived from it),
`github_pat` (needs `read:packages`; distinct from the git-sync PAT).

## Verify

```bash
az k8s-configuration flux show --resource-group rg-{{ cookiecutter.project_slug }} \
  --cluster-name aks-{{ cookiecutter.project_slug }} --cluster-type managedClusters \
  --name {{ cookiecutter.project_slug }}

kubectl get kustomizations -n flux-system      # all Ready
kubectl get helmreleases -A                    # all Ready (vault: see step 4)
kubectl get clusters.postgresql.cnpg.io -n {{ cookiecutter.project_slug }}
kubectl get pods -n {{ cookiecutter.project_slug }}
```
