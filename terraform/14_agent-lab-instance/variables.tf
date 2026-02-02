variable "agent_lab_namespace" {
  description = "Kubernetes namespace for app deployment"
  type        = string
  default     = "agent-lab"
}

variable "vault_url" {
  description = "URL of Vault instance"
  type        = string
}

variable "vault_engine_path" {
  description = "Engine Path used inside Vault instance"
  type        = string
  default     = "secret"
}

variable "vault_secret_path" {
  description = "Secret Path used inside Vault instance"
  type        = string
  default     = "app_secrets"
}

variable "vault_api_key" {
  description = "API KEY token of Vault instance"
  type        = string
  sensitive   = true
}

variable "vault_secret_value_broker_url" {
  description = "Redis Broker URL"
  type        = string
  sensitive   = true
  default     = "redis://redis-agent-lab.agent-lab.svc.cluster.local:6379/0"
}

variable "vault_secret_value_cdp_url" {
  description = "Chrome Development Protocol URL"
  type        = string
  sensitive   = true
  default     = "http://cdp-agent-lab.agent-lab.svc.cluster.local:9222"
}

variable "langwatch_endpoint" {
  description = "Endpoint URL of Langwatch instance"
  type        = string
  default     = "http://langwatch-app.langwatch.svc.cluster.local:5560"
}

# variable "langwatch_api_key" {
#   description = "API KEY token of Vault instance"
#   type        = string
# }

variable "pg_image" {
  type        = string
  default     = "bsantanna/cloudnative-pg-vector:17.4"
  description = "PostgreSQL image with pgvector (adjust if needed)"
}
