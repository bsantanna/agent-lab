variable "subscription_id" {
  description = "Azure subscription to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region to deploy into"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group for the AKS cluster"
  type        = string
  default     = "rg-{{ cookiecutter.project_slug }}"
}

variable "cluster_name" {
  description = "AKS cluster name"
  type        = string
  default     = "aks-{{ cookiecutter.project_slug }}"
}

variable "sku_tier" {
  description = "AKS control plane pricing tier: Free (no management fee, no SLA) or Standard"
  type        = string
  default     = "Free"
}

variable "system_node_pool_name" {
  description = "Name of the system node pool"
  type        = string
  default     = "system"
}

variable "system_node_vm_size" {
  description = "VM size for the system node pool"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "system_node_min_count" {
  description = "Minimum node count for the system pool autoscaler"
  type        = number
  default     = 1
}

variable "system_node_max_count" {
  description = "Maximum node count for the system pool autoscaler"
  type        = number
  default     = 3
}

variable "system_node_os_disk_type" {
  description = "OS disk type for system pool nodes. Ephemeral fits in the Standard_D2s_v3 cache (50 GiB) and avoids the default 128 GiB Premium managed disk per node; use Managed for VM sizes without a cache disk."
  type        = string
  default     = "Ephemeral"
}

variable "system_node_os_disk_size_gb" {
  description = "OS disk size for system pool nodes; must fit within the VM cache size when os_disk_type is Ephemeral"
  type        = number
  default     = 30
}

variable "user_node_pool_name" {
  description = "Name of the user node pool"
  type        = string
  default     = "user"
}

variable "user_node_vm_size" {
  description = "VM size for the user node pool"
  type        = string
  default     = "Standard_B2s"
}

variable "user_node_count" {
  description = "Node count for the user pool"
  type        = number
  default     = 1
}

variable "user_node_os_disk_size_gb" {
  description = "OS disk size for user pool nodes; stays a managed disk because Standard_B2s has no cache disk for ephemeral"
  type        = number
  default     = 32
}

variable "unseal_key_vault_name" {
  description = "Globally unique name (3-24 chars) of the Azure Key Vault holding the Vault auto-unseal key; override if the slug-derived default is too long"
  type        = string
  default     = "kv-{{ cookiecutter.project_slug }}-unseal"
}

variable "unseal_key_name" {
  description = "Name of the RSA key used by Vault's azurekeyvault seal"
  type        = string
  default     = "vault-unseal"
}
