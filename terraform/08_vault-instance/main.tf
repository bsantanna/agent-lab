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

resource "kubernetes_namespace_v1" "vault" {
  metadata {
    name = "vault"
  }
}

resource "helm_release" "vault" {
  name       = "vault"
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  namespace  = kubernetes_namespace_v1.vault.metadata[0].name
  # version    = "0.31.0"

  values = [
    yamlencode({
      server = {
        ingress = {
          enabled = true

          ingressClassName = "traefik"

          annotations = {
            "cert-manager.io/cluster-issuer"                   = "letsencrypt-prod"
            "traefik.ingress.kubernetes.io/router.entrypoints" = "websecure"
            "traefik.ingress.kubernetes.io/router.tls"         = "true"
          }

          hosts = [
            {
              host  = var.vault_hostname
              paths = ["/"]
            }
          ]

          tls = [
            {
              secretName = "vault-tls-secret"
              hosts      = [var.vault_hostname]
            }
          ]
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.vault]
}
