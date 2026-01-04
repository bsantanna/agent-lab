variable "agent_lab_namespace" {
  description = "Kubernetes namespace for app deployment"
  type        = string
  default     = "agent-lab"
}

variable "vault_endpoint" {
  description = "Endpoint URL of Vault instance"
  type        = string
  default     = "http://vault.vault.svc.cluster.local:8200"
}

# variable "vault_api_key" {
#   description = "API KEY token of Vault instance"
#   type        = string
# }

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
