variable "agent_lab_namespace" {
  description = "Kubernetes namespace for app deployment"
  type        = string
  default     = "agent-lab"
}

variable "pg_image" {
  type        = string
  default     = "bsantanna/cloudnative-pg-vector:17.4"
  description = "PostgreSQL image with pgvector (adjust if needed)"
}
