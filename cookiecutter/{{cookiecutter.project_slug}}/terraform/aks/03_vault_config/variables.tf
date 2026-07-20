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

variable "vault_hostname" {
  description = "Public hostname of the Vault ingress (same value as 02_gitops); the vault provider connects to https://<hostname>"
  type        = string
}

variable "vault_token" {
  description = "Vault token with rights to manage mounts, policies, and auth backends (the initial root token, or an admin token derived from it). Supply via TF_VAR_vault_token or a local tfvars file; never commit it."
  type        = string
  sensitive   = true
}

variable "github_user" {
  description = "Username for GHCR image pulls; any non-empty value works with a PAT"
  type        = string
  default     = "git"
}

variable "github_pat" {
  description = "GitHub PAT with read:packages for pulling the app image from GHCR. Supply via TF_VAR_github_pat or a local tfvars file; never commit it."
  type        = string
  sensitive   = true
}

variable "api_base_url" {
  description = "Base URL the app advertises; cluster-internal service URL until an app ingress exists"
  type        = string
  default     = "http://{{ cookiecutter.project_slug }}.{{ cookiecutter.project_slug }}.svc.cluster.local"
}
