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

resource "kubernetes_namespace_v1" "traefik" {
  metadata {
    name = "traefik"
  }
}

resource "helm_release" "traefik" {
  name       = "traefik"
  repository = "https://traefik.github.io/charts"
  chart      = "traefik"
  namespace  = kubernetes_namespace_v1.traefik.metadata[0].name

  values = [
    yamlencode({
      ports = {
        web = {
          port     = 8000
          nodePort = 30080
          protocol = "TCP"
        }
        websecure = {
          port     = 8443
          nodePort = 30443
          protocol = "TCP"
        }
        traefik = {
          port = 9000
        }
      }

      service = {
        enabled = true
        type    = "NodePort"
      }

      securityContext = {
        capabilities = {
          drop = ["ALL"]
          add  = ["NET_BIND_SERVICE"]
        }
        readOnlyRootFilesystem = true
        runAsNonRoot           = true
      }

      providers = {
        kubernetesCRD     = { enabled = true }
        kubernetesIngress = { enabled = true }
      }

      logs = {
        general = { level = "INFO" }
      }

      persistence = {
        enabled = false
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.traefik]
}
