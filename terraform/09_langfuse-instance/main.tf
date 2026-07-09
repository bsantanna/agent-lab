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
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
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

resource "kubernetes_namespace_v1" "langfuse" {
  metadata {
    name = "langfuse"
  }
}

# Langfuse application secrets. NEXTAUTH_SECRET and SALT are opaque tokens;
# ENCRYPTION_KEY must be a 256-bit key encoded as 64 hex characters.
resource "random_password" "nextauth_secret" {
  length  = 32
  special = false
}

resource "random_password" "salt" {
  length  = 32
  special = false
}

resource "random_id" "encryption_key" {
  byte_length = 32
}

resource "helm_release" "langfuse" {
  name       = "langfuse"
  repository = "https://langfuse.github.io/langfuse-k8s"
  chart      = "langfuse"
  namespace  = kubernetes_namespace_v1.langfuse.metadata[0].name

  # Datastores (Postgres, Redis, ClickHouse, S3/MinIO) are chart-managed and
  # bundled by default, mirroring the self-contained self-hosting quickstart.
  values = [
    yamlencode({
      langfuse = {
        nextauth = {
          url = "https://${var.langfuse_fqdn}"
          secret = {
            value = random_password.nextauth_secret.result
          }
        }
        salt = {
          value = random_password.salt.result
        }
        encryptionKey = {
          value = random_id.encryption_key.hex
        }
        ingress = {
          enabled = false
        }
      }

      postgresql = {
        deploy = true
      }

      clickhouse = {
        deploy = true
      }

      redis = {
        deploy = true
      }

      s3 = {
        deploy = true
      }
    })
  ]

  timeout = 600

  depends_on = [kubernetes_namespace_v1.langfuse]
}

resource "kubernetes_ingress_v1" "langfuse" {
  metadata {
    name      = "langfuse"
    namespace = kubernetes_namespace_v1.langfuse.metadata[0].name

    annotations = {
      "cert-manager.io/cluster-issuer"                   = "letsencrypt-prod"
      "traefik.ingress.kubernetes.io/router.entrypoints" = "websecure"
      "traefik.ingress.kubernetes.io/router.tls"         = "true"
    }
  }

  spec {
    ingress_class_name = "traefik"

    tls {
      hosts       = [var.langfuse_fqdn]
      secret_name = "langfuse-tls"
    }

    rule {
      host = var.langfuse_fqdn

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = "langfuse-web"
              port {
                number = 3000
              }
            }
          }
        }
      }
    }
  }

  depends_on = [helm_release.langfuse]
}
