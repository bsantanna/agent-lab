variable "langfuse_fqdn" {
  type        = string
  description = "FQDN for Langfuse access (e.g., langfuse.local or a public domain)"
}

variable "pg_image" {
  type        = string
  default     = "bsantanna/cloudnative-pg-vector:17.4"
  description = "PostgreSQL image with pgvector (adjust if needed)"
}
