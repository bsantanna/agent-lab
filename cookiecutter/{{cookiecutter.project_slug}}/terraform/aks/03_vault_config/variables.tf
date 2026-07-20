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
  description = "Public hostname of the Vault ingress (same value as 02_gitops); used by the vault_init step and the vault provider via https://<hostname>"
  type        = string
}

variable "unseal_key_vault_name" {
  description = "Name of the Azure Key Vault (managed by 01_aks) holding the Vault init payload; must match the 01_aks value"
  type        = string
  default     = "kv-{{ cookiecutter.project_slug }}-unseal"
}

variable "init_secret_name" {
  description = "Key Vault secret name written by this stage's vault_init step; its JSON value provides the Vault root token"
  type        = string
  default     = "vault-init"
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

variable "app_hostname" {
  description = "Public hostname of the app ingress (same value as 02_gitops); used for api_base_url"
  type        = string
}
{%- if cookiecutter.auth_enabled %}

variable "auth_url" {
  description = "Base URL of the OIDC provider the app authenticates against (e.g. https://auth.example.com)"
  type        = string
}

variable "auth_realm" {
  description = "Realm on the OIDC provider"
  type        = string
  default     = "{{ cookiecutter.project_slug }}"
}

variable "auth_client_id" {
  description = "OIDC client id the app uses"
  type        = string
  default     = "{{ cookiecutter.project_slug }}"
}

variable "auth_client_secret" {
  description = "OIDC client secret for the app. Supply via TF_VAR_auth_client_secret or a local tfvars file; never commit it."
  type        = string
  sensitive   = true
}
{%- endif %}
