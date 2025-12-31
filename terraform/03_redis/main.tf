
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


resource "kubernetes_namespace_v1" "ot_operators" {
  metadata {
    name = "ot-operators"
  }
}

resource "helm_release" "redis_operator" {
  name       = "redis-operator"
  repository = "https://ot-container-kit.github.io/helm-charts/"
  chart      = "redis-operator"
  namespace  = kubernetes_namespace_v1.ot_operators.metadata[0].name


  set = [{
    name  = "featureGates.GenerateConfigInInitContainer"
    value = "true"
  }]

  depends_on = [kubernetes_namespace_v1.ot_operators]
}
