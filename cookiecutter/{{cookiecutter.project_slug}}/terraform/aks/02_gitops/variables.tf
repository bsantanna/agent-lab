variable "subscription_id" {
  description = "Azure subscription to deploy into"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group of the AKS cluster managed by 01_aks"
  type        = string
  default     = "rg-{{ cookiecutter.project_slug }}"
}

variable "cluster_name" {
  description = "Name of the AKS cluster managed by 01_aks"
  type        = string
  default     = "aks-{{ cookiecutter.project_slug }}"
}

variable "flux_configuration_name" {
  description = "Name of the Flux configuration on the cluster"
  type        = string
  default     = "{{ cookiecutter.project_slug }}"
}

variable "flux_namespace" {
  description = "Namespace the Flux configuration objects are created in"
  type        = string
  default     = "flux-system"
}

variable "kustomization_name" {
  description = "Name of the Flux kustomization that applies the gitops path"
  type        = string
  default     = "apps"
}

variable "git_repository_url" {
  description = "HTTPS URL of the git repository Flux syncs from"
  type        = string
  default     = "https://github.com/{{ cookiecutter.github_repository }}"
}

variable "git_branch" {
  description = "Branch Flux tracks"
  type        = string
  default     = "main"
}

variable "gitops_path" {
  description = "Path within the repository containing the kustomize manifests"
  type        = string
  default     = "./gitops"
}

variable "cert_manager_email" {
  description = "Email for the Let's Encrypt ClusterIssuer; substituted into gitops manifests via Flux postBuild"
  type        = string
}

variable "vault_hostname" {
  description = "Public hostname for the Vault ingress (DNS must point at the traefik load balancer); substituted into gitops manifests via Flux postBuild"
  type        = string
}

variable "pg_image" {
  description = "PostgreSQL image with pgvector used by the CNPG clusters; substituted into gitops manifests via Flux postBuild"
  type        = string
  default     = "bsantanna/cloudnative-pg-vector:17.4"
}

variable "unseal_key_vault_name" {
  description = "Name of the Azure Key Vault holding the Vault auto-unseal key, managed by 01_aks; substituted into gitops manifests via Flux postBuild"
  type        = string
  default     = "kv-{{ cookiecutter.project_slug }}-unseal"
}

variable "unseal_key_name" {
  description = "Name of the RSA unseal key in the Key Vault, managed by 01_aks; substituted into gitops manifests via Flux postBuild"
  type        = string
  default     = "vault-unseal"
}

variable "github_user" {
  description = "Username for HTTPS git auth; any non-empty value works with a PAT"
  type        = string
  default     = "git"
}

variable "github_pat" {
  description = "GitHub fine-grained PAT with read-only Contents access to the repository. Supply via TF_VAR_github_pat or a local tfvars file; never commit it."
  type        = string
  sensitive   = true
}
