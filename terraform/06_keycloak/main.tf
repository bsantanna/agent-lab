

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


resource "kubernetes_namespace_v1" "keycloak" {
  metadata {
    name = "keycloak"
  }
}


resource "helm_release" "pg_keycloak" {
  name       = "pg-keycloak"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = kubernetes_namespace_v1.keycloak.metadata[0].name

  values = [
    yamlencode({
      cluster = {
        imageName = "bsantanna/cloudnative-pg-vector:17.4"
        instances = 1
        storage = {
          size = "1Gi"
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.keycloak]
}

data "kubernetes_secret_v1" "pg_app_secret" {
  metadata {
    name      = "${helm_release.pg_keycloak.name}-cluster-app"
    namespace = helm_release.pg_keycloak.namespace
  }

  depends_on = [helm_release.pg_keycloak]
}


