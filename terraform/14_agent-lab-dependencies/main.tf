
terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = ">= 3.0.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.9.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = ">= 4.0.0"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes = {
    config_path = "~/.kube/config"
  }
}

provider "vault" {
  address = var.vault_url
  token   = var.vault_api_key
}

resource "helm_release" "pg_agent-lab-app" {
  name       = "pg-agent-lab-app"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = var.agent_lab_namespace

  values = [
    yamlencode({
      cluster = {
        instances = 1
        imageName = var.pg_image
        storage = {
          size = "5Gi"
        }
      }
    })
  ]

}

resource "helm_release" "pg_agent-lab-vectors" {
  name       = "pg-agent-lab-vectors"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = var.agent_lab_namespace

  values = [
    yamlencode({
      cluster = {
        instances = 1
        imageName = var.pg_image
        storage = {
          size = "5Gi"
        }
      }
    })
  ]

}

resource "helm_release" "pg_agent-lab-checkpoints" {
  name       = "pg-agent-lab-checkpoints"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = var.agent_lab_namespace

  values = [
    yamlencode({
      cluster = {
        instances = 1
        imageName = var.pg_image
        storage = {
          size = "5Gi"
        }
      }
    })
  ]

}

data "kubernetes_secret_v1" "auth_secrets" {
  metadata {
    name      = "agent-lab-auth"
    namespace = var.agent_lab_namespace
  }
}

resource "time_sleep" "wait_for_pg_secrets" {
  create_duration = "15s"

  depends_on = [
    helm_release.pg_agent-lab-app,
    helm_release.pg_agent-lab-vectors,
    helm_release.pg_agent-lab-checkpoints
  ]
}

data "kubernetes_secret_v1" "pg_agent-lab-app-secret" {
  metadata {
    name      = "${helm_release.pg_agent-lab-app.name}-cluster-app"
    namespace = var.agent_lab_namespace
  }

  depends_on = [time_sleep.wait_for_pg_secrets]
}

data "kubernetes_secret_v1" "pg_agent-lab-vectors-secret" {
  metadata {
    name      = "${helm_release.pg_agent-lab-vectors.name}-cluster-app"
    namespace = var.agent_lab_namespace
  }

  depends_on = [time_sleep.wait_for_pg_secrets]
}

data "kubernetes_secret_v1" "pg_agent-lab-checkpoints-secret" {
  metadata {
    name      = "${helm_release.pg_agent-lab-checkpoints.name}-cluster-app"
    namespace = var.agent_lab_namespace
  }

  depends_on = [time_sleep.wait_for_pg_secrets]
}

resource "helm_release" "redis_agent_lab" {
  name       = "redis-agent-lab"
  repository = "https://ot-container-kit.github.io/helm-charts/"
  chart      = "redis"
  namespace  = var.agent_lab_namespace


  set = [{
    name  = "featureGates.GenerateConfigInInitContainer"
    value = "true"
  }]

}

resource "time_sleep" "wait_for_redis" {
  create_duration = "15s"

  depends_on = [
    helm_release.redis_agent_lab
  ]
}

resource "kubernetes_secret_v1" "agent_lab_secret" {
  metadata {
    name      = "agent-lab-secret"
    namespace = var.agent_lab_namespace
  }

  # APP BOOT dependencies
  data = {
    VAULT_URL          = var.vault_url
    VAULT_TOKEN        = var.vault_api_key
    VAULT_ENGINE_PATH  = var.vault_engine_path
    VAULT_SECRET_PATH  = var.vault_secret_path
    LANGWATCH_ENDPOINT = var.langwatch_endpoint
    LANGWATCH_API_KEY  = var.langwatch_api_key
  }

  type = "Opaque"
}

resource "vault_mount" "kv" {
  path        = var.vault_engine_path
  type        = "kv"
  description = "KV Version 2 secret engine for Agent-Lab"

  options = {
    version = "2"
  }
}

resource "vault_kv_secret_v2" "app_secrets" {
  mount = vault_mount.kv.path
  name  = var.vault_secret_path

  data_json = jsonencode({
    api_base_url = var.agent_lab_fqdn

    # Auth secrets
    auth_enabled       = true
    auth_url           = data.kubernetes_secret_v1.auth_secrets.data["AUTH_URL"]
    auth_realm         = data.kubernetes_secret_v1.auth_secrets.data["AUTH_REALM"]
    auth_client_id     = data.kubernetes_secret_v1.auth_secrets.data["AUTH_CLIENT_ID"]
    auth_client_secret = data.kubernetes_secret_v1.auth_secrets.data["AUTH_CLIENT_SECRET"]

    # PostgreSQL App database
    db_url = "postgresql://${data.kubernetes_secret_v1.pg_agent-lab-app-secret.data["username"]}:${data.kubernetes_secret_v1.pg_agent-lab-app-secret.data["password"]}@${helm_release.pg_agent-lab-app.name}-cluster-rw.${var.agent_lab_namespace}.svc.cluster.local:5432/app"

    # PostgreSQL Vectors database
    db_vectors = "postgresql://${data.kubernetes_secret_v1.pg_agent-lab-vectors-secret.data["username"]}:${data.kubernetes_secret_v1.pg_agent-lab-vectors-secret.data["password"]}@${helm_release.pg_agent-lab-vectors.name}-cluster-rw.${var.agent_lab_namespace}.svc.cluster.local:5432/app"

    # PostgreSQL Checkpoints database
    db_checkpoints = "postgresql://${data.kubernetes_secret_v1.pg_agent-lab-checkpoints-secret.data["username"]}:${data.kubernetes_secret_v1.pg_agent-lab-checkpoints-secret.data["password"]}@${helm_release.pg_agent-lab-checkpoints.name}-cluster-rw.${var.agent_lab_namespace}.svc.cluster.local:5432/app"

    # Redis broker
    broker_url = var.vault_secret_value_broker_url

    # Chrome DevTools Protocol
    cdp_url = var.vault_secret_value_cdp_url

    # Tavily API KEY
    tavily_api_key = var.vault_secret_value_tavily_api_key
  })

  depends_on = [
    vault_mount.kv,
    data.kubernetes_secret_v1.auth_secrets,
    data.kubernetes_secret_v1.pg_agent-lab-app-secret,
    data.kubernetes_secret_v1.pg_agent-lab-vectors-secret,
    data.kubernetes_secret_v1.pg_agent-lab-checkpoints-secret
  ]

}
