
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

resource "kubernetes_namespace_v1" "agent_lab" {
  metadata {
    name = var.agent_lab_namespace
  }
}

resource "helm_release" "pg_agent-lab-app" {
  name       = "pg-agent-lab-app"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = kubernetes_namespace_v1.agent_lab.metadata[0].name

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

  depends_on = [kubernetes_namespace_v1.agent_lab]
}

resource "helm_release" "pg_agent-lab-vectors" {
  name       = "pg-agent-lab-vectors"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = kubernetes_namespace_v1.agent_lab.metadata[0].name

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

  depends_on = [kubernetes_namespace_v1.agent_lab]
}

resource "helm_release" "pg_agent-lab-checkpoints" {
  name       = "pg-agent-lab-checkpoints"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = kubernetes_namespace_v1.agent_lab.metadata[0].name

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

  depends_on = [kubernetes_namespace_v1.agent_lab]
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
    namespace = kubernetes_namespace_v1.agent_lab.metadata[0].name
  }

  depends_on = [time_sleep.wait_for_pg_secrets]
}

data "kubernetes_secret_v1" "pg_agent-lab-vectors-secret" {
  metadata {
    name      = "${helm_release.pg_agent-lab-vectors.name}-cluster-app"
    namespace = kubernetes_namespace_v1.agent_lab.metadata[0].name
  }

  depends_on = [time_sleep.wait_for_pg_secrets]
}

data "kubernetes_secret_v1" "pg_agent-lab-checkpoints-secret" {
  metadata {
    name      = "${helm_release.pg_agent-lab-checkpoints.name}-cluster-app"
    namespace = kubernetes_namespace_v1.agent_lab.metadata[0].name
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

  depends_on = [kubernetes_namespace_v1.agent_lab]
}

resource "time_sleep" "wait_for_redis_secret" {
  create_duration = "15s"

  depends_on = [
    helm_release.redis_agent_lab
  ]
}

resource "kubernetes_secret_v1" "redis_conn" {
  metadata {
    name      = "redis-conn"
    namespace = kubernetes_namespace_v1.agent_lab.metadata[0].name
  }

  data = {
    url = "redis://redis-agent-lab.${kubernetes_namespace_v1.agent_lab.metadata[0].name}.svc.cluster.local:6379/0"
  }

  type = "Opaque"
}

