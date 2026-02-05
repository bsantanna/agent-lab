

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

resource "kubernetes_namespace_v1" "elastic_system" {
  metadata {
    name = "elastic-system"
  }
}

resource "helm_release" "eck-operator" {
  name       = "elastic"
  repository = "https://helm.elastic.co"
  chart      = "eck-operator"
  namespace  = kubernetes_namespace_v1.elastic_system.metadata[0].name
  depends_on = [kubernetes_namespace_v1.elastic_system]
}
