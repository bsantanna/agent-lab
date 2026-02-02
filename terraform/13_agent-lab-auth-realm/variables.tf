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
