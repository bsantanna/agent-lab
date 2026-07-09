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

resource "kubernetes_namespace_v1" "langfuse" {
  metadata {
    name = "langfuse"
  }
}

# Operator-managed PostgreSQL (CloudNativePG), mirroring the langwatch module.
# The operator provisions a `<name>-cluster-app` secret holding the `app` user
# credentials, which Langfuse consumes directly via postgresql.auth.existingSecret.
resource "helm_release" "pg_langfuse" {
  name       = "pg-langfuse"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = kubernetes_namespace_v1.langfuse.metadata[0].name

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

  depends_on = [kubernetes_namespace_v1.langfuse]
}

resource "time_sleep" "wait_for_pg_secret" {
  create_duration = "15s"

  depends_on = [helm_release.pg_langfuse]
}

# Operator-managed Redis (OT container-kit), mirroring the langwatch module.
# Deployed passwordless, so Langfuse connects with a plain redis://host:port URL.
resource "helm_release" "redis_langfuse" {
  name       = "redis-langfuse"
  repository = "https://ot-container-kit.github.io/helm-charts/"
  chart      = "redis"
  namespace  = kubernetes_namespace_v1.langfuse.metadata[0].name

  set = [{
    name  = "featureGates.GenerateConfigInInitContainer"
    value = "true"
  }]

  depends_on = [kubernetes_namespace_v1.langfuse]
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

# Passwords for the datastores that stay chart-managed (no operator upstream):
# the bundled ClickHouse and MinIO subcharts require an explicit password.
# special = false keeps them safe to embed without URL-encoding.
resource "random_password" "clickhouse" {
  length  = 24
  special = false
}

resource "random_password" "minio" {
  length  = 24
  special = false
}

resource "helm_release" "langfuse" {
  name       = "langfuse"
  repository = "https://langfuse.github.io/langfuse-k8s"
  chart      = "langfuse"
  namespace  = kubernetes_namespace_v1.langfuse.metadata[0].name

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

      # External Postgres provisioned by CloudNativePG. Username/database are the
      # operator's defaults (`app`); the password is read from the operator secret.
      postgresql = {
        deploy = false
        host   = "${helm_release.pg_langfuse.name}-cluster-rw.${kubernetes_namespace_v1.langfuse.metadata[0].name}.svc.cluster.local"
        port   = 5432
        auth = {
          username       = "app"
          database       = "app"
          existingSecret = "${helm_release.pg_langfuse.name}-cluster-app"
          secretKeys = {
            userPasswordKey  = "password"
            adminPasswordKey = "password"
          }
        }
      }

      # External passwordless Redis provisioned by the OT operator. username is
      # nulled so the chart emits a clean redis://host:port/0 (no auth segment).
      redis = {
        deploy = false
        host   = "${helm_release.redis_langfuse.name}.${kubernetes_namespace_v1.langfuse.metadata[0].name}.svc.cluster.local"
        port   = 6379
        auth = {
          username = null
          password = ""
        }
      }

      # Single-node ClickHouse: the chart defaults to 3 replicas + a 3-node
      # Zookeeper subchart + a 2xlarge preset. Collapse to one non-HA node with
      # no Zookeeper (not needed without replication) and a small preset.
      clickhouse = {
        deploy          = true
        clusterEnabled  = false
        replicaCount    = 1
        resourcesPreset = "small"
        zookeeper = {
          enabled = false
        }
        auth = {
          password = random_password.clickhouse.result
        }
      }

      # Bundled MinIO. endpoint, bucket (defaultBuckets) and accessKeyId
      # (rootUser) are auto-derived by the chart when deploy = true; only the
      # root password must be supplied.
      s3 = {
        deploy = true
        auth = {
          rootPassword = random_password.minio.result
        }
      }
    })
  ]

  timeout = 600

  depends_on = [
    time_sleep.wait_for_pg_secret,
    helm_release.redis_langfuse
  ]
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
