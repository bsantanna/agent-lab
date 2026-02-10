terraform {
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = ">= 5.0.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
}

provider "keycloak" {
  client_id = "admin-cli"
  username  = var.auth_admin_username
  password  = var.auth_admin_secret
  url       = var.auth_url
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_namespace_v1" "agent_lab" {
  metadata {
    name = var.agent_lab_namespace
  }
}

resource "keycloak_realm" "agent_lab" {
  realm   = var.auth_realm
  enabled = true

  display_name      = "Agent-Lab"
  display_name_html = "<strong>Agent-Lab</strong>"

  login_theme   = "keycloak"
  account_theme = "keycloak.v3"
  admin_theme   = "keycloak.v2"
  email_theme   = "keycloak"

  access_code_lifespan = "1h"

  access_token_lifespan        = "168h"
  sso_session_idle_timeout     = "168h"
  sso_session_max_lifespan     = "168h"
  offline_session_idle_timeout = "168h"
  offline_session_max_lifespan = "168h"
  refresh_token_max_reuse      = 0

  ssl_required    = "external"
  password_policy = "upperCase(1) and length(8) and forceExpiredPasswordChange(365) and notUsername"

  internationalization {
    supported_locales = ["en"]
    default_locale    = "en"
  }

  security_defenses {
    headers {
      x_frame_options                     = "SAMEORIGIN"
      content_security_policy             = "frame-src 'self'; frame-ancestors 'self'; object-src 'none';"
      content_security_policy_report_only = ""
      x_content_type_options              = "nosniff"
      x_robots_tag                        = "none"
      x_xss_protection                    = "1; mode=block"
      strict_transport_security           = "max-age=31536000; includeSubDomains"
    }
    brute_force_detection {
      permanent_lockout                = false
      max_login_failures               = 30
      wait_increment_seconds           = 60
      quick_login_check_milli_seconds  = 1000
      minimum_quick_login_wait_seconds = 60
      max_failure_wait_seconds         = 900
      failure_reset_time_seconds       = 43200
    }
  }
}

resource "keycloak_openid_client" "agent_lab_client" {
  realm_id  = keycloak_realm.agent_lab.id
  client_id = var.auth_client_id
  name      = var.auth_client_id
  enabled   = true

  access_type                  = "CONFIDENTIAL"
  standard_flow_enabled        = true
  direct_access_grants_enabled = true
  service_accounts_enabled     = true

  valid_redirect_uris = var.auth_client_redirect_uris

  login_theme = "keycloak"
}

resource "keycloak_user" "service_account" {
  realm_id   = keycloak_realm.agent_lab.id
  username   = var.auth_service_account_username
  enabled    = true
  first_name = "Service"
  last_name  = "Account"

  email          = "${var.auth_service_account_username}@agent-lab.local"
  email_verified = true

  initial_password {
    value     = var.auth_service_account_secret
    temporary = false
  }
}

resource "kubernetes_secret_v1" "agent_lab_auth" {
  metadata {
    name      = "agent-lab-auth"
    namespace = var.agent_lab_namespace
  }

  data = {
    AUTH_URL           = var.auth_url
    AUTH_REALM         = keycloak_realm.agent_lab.realm
    AUTH_CLIENT_ID     = keycloak_openid_client.agent_lab_client.client_id
    AUTH_CLIENT_SECRET = keycloak_openid_client.agent_lab_client.client_secret
  }

  type = "Opaque"
}
