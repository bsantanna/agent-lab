variable "agent_lab_namespace" {
  description = "Kubernetes namespace for app deployment"
  type        = string
  default     = "agent-lab"
}

variable "agent_lab_chart_version" {
  description = "Helm chart version for agent-lab"
  type        = string
  default     = "1.5.0"
}

variable "agent_lab_image_tag" {
  description = "Docker image tag for agent-lab"
  type        = string
  default     = "v1.5.0"
}

variable "agent_lab_fqdn" {
  description = "Fully qualified domain name for agent-lab ingress"
  type        = string
}

variable "telemetry_endpoint" {
  description = "OpenTelemetry collector endpoint URL"
  type        = string
  default     = "http://otel-collector-opentelemetry-collector.otel.svc.cluster.local:4318"
}
