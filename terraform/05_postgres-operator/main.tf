
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


resource "kubernetes_namespace_v1" "cnpg_system" {
  metadata {
    name = "cnpg-system"
  }
}


resource "helm_release" "cnpg" {
  name       = "cnpg"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cloudnative-pg"
  namespace  = kubernetes_namespace_v1.cnpg_system.metadata[0].name
  version    = "0.27.0"




  depends_on = [kubernetes_namespace_v1.cnpg_system]
}
