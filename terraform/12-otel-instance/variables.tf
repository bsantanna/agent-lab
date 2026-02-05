variable "otlp_http_endpoint" {
  type        = string
  default     = "https://elastic-eck-apm-server-apm-http:8200"
  description = "Endpoint for OTLP HTTP exporter"
}

variable "otlp_http_auth_token" {
  type        = string
  description = "Authentication token for OTLP HTTP exporter"
  sensitive   = true
}
