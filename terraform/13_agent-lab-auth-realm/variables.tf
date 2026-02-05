variable "agent_lab_namespace" {
  description = "Kubernetes namespace for app deployment"
  type        = string
  default     = "agent-lab"
}

variable "auth_url" {
  type        = string
  description = "Auth Host URL"
}

variable "auth_realm" {
  type        = string
  description = "Auth Realm"
  default     = "agent-lab"
}

variable "auth_admin_username" {
  type        = string
  description = "Auth Admin Username"
  sensitive   = true
}

variable "auth_admin_secret" {
  type        = string
  description = "Auth Admin Secret"
  sensitive   = true
}

variable "auth_service_account_username" {
  type        = string
  description = "Auth Service Account Username"
  default     = "agent-lab-service-account"
  sensitive   = true
}

variable "auth_service_account_secret" {
  type        = string
  description = "Auth Service Account Secret"
  sensitive   = true
}

variable "auth_client_id" {
  type        = string
  description = "Auth Client ID"
  default     = "agent-lab-client"
}

variable "auth_client_redirect_uris" {
  type        = list(string)
  description = "Auth Client Redirect URIs"
  default     = ["*"]
}
