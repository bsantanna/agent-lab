variable "keycloak_version" {
  description = "Keycloak version (matches operator bundle tag and container image tag)"
  type        = string
  default     = "26.0.0"
}

variable "keycloak_hostname" {
  description = "Full hostname for Keycloak (e.g., keycloak.example.com). This will be used for the ingress and frontend URL."
  type        = string
}

variable "keycloak_image" {
  description = "Custom optimized Keycloak image for Postgres (REQUIRED for versions 23+ to avoid DB startup errors)"
  type        = string
  default     = "bsantanna/keycloak:26.0.0"
}
