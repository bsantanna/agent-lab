variable "keycloak_version" {
  description = "Keycloak version (matches operator bundle tag and container image tag)"
  type        = string
  default     = "26.0.0"
}

variable "keycloak_hostname" {
  description = "Full hostname for Keycloak (e.g., keycloak.example.com). This will be used for the ingress and frontend URL."
  type        = string
}
