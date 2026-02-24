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

resource "kubernetes_namespace_v1" "langwatch" {
  metadata {
    name = "langwatch"
  }
}


resource "helm_release" "pg_langwatch" {
  name       = "pg-langwatch"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = kubernetes_namespace_v1.langwatch.metadata[0].name

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

  depends_on = [kubernetes_namespace_v1.langwatch]
}

resource "time_sleep" "wait_for_pg_secret" {
  create_duration = "15s"

  depends_on = [helm_release.pg_langwatch]
}

data "kubernetes_secret_v1" "pg_app_secret" {
  metadata {
    name      = "${helm_release.pg_langwatch.name}-cluster-app"
    namespace = kubernetes_namespace_v1.langwatch.metadata[0].name
  }

  depends_on = [time_sleep.wait_for_pg_secret]
}

resource "kubernetes_secret_v1" "pg_conn" {
  metadata {
    name      = "pg-conn"
    namespace = kubernetes_namespace_v1.langwatch.metadata[0].name
  }

  data = {
    url = "postgresql://${data.kubernetes_secret_v1.pg_app_secret.data["username"]}:${data.kubernetes_secret_v1.pg_app_secret.data["password"]}@${helm_release.pg_langwatch.name}-cluster-rw.${kubernetes_namespace_v1.langwatch.metadata[0].name}.svc.cluster.local:5432/app"
  }

  type = "Opaque"

  depends_on = [data.kubernetes_secret_v1.pg_app_secret]
}

resource "helm_release" "redis_langwatch" {
  name       = "redis-langwatch"
  repository = "https://ot-container-kit.github.io/helm-charts/"
  chart      = "redis"
  namespace  = kubernetes_namespace_v1.langwatch.metadata[0].name


  set = [{
    name  = "featureGates.GenerateConfigInInitContainer"
    value = "true"
  }]

  depends_on = [kubernetes_namespace_v1.langwatch]
}



resource "kubernetes_secret_v1" "redis_conn" {
  metadata {
    name      = "redis-conn"
    namespace = kubernetes_namespace_v1.langwatch.metadata[0].name
  }

  data = {
    url = "redis://redis-langwatch.langwatch.svc.cluster.local:6379/0"
  }

  type = "Opaque"
}

resource "helm_release" "langwatch" {
  name       = "langwatch"
  repository = "https://langwatch.github.io/langwatch/"
  chart      = "langwatch-helm"
  namespace  = kubernetes_namespace_v1.langwatch.metadata[0].name

  values = [
    yamlencode({
      global = {
        env = "production"
      }

      autogen = {
        enabled = true
      }

      app = {
        http = {
          publicUrl = "https://${var.langwatch_fqdn}"
          baseHost  = "https://${var.langwatch_fqdn}"
        }
        podSecurityContext = {
          runAsNonRoot = false
          runAsUser    = 0
          fsGroup      = 0
        }
        containerSecurityContext = {
          allowPrivilegeEscalation = false
          capabilities = {
            drop = ["ALL"]
          }
          readOnlyRootFilesystem = false
        }
      }

      ingress = {
        enabled = false
      }

      postgresql = {
        chartManaged = false
        external = {
          connectionString = {
            secretKeyRef = {
              name = "pg-conn"
              key  = "url"
            }
          }
        }
      }

      redis = {
        chartManaged = false
        external = {
          connectionString = {
            secretKeyRef = {
              name = "redis-conn"
              key  = "url"
            }
          }
        }
      }

      opensearch = {
        chartManaged = true
        replicas     = 1
        persistence = {
          enabled = true
          size    = "10Gi"
        }
      }

      prometheus = {
        chartManaged = true
      }

      langevals = {
        podSecurityContext = {
          runAsNonRoot = false
          runAsUser    = 0
          fsGroup      = 0
        }
        containerSecurityContext = {
          allowPrivilegeEscalation = false
          capabilities = {
            drop = ["ALL"]
          }
          readOnlyRootFilesystem = false
        }
      }

      workers = {
        enabled = false
      }
    })
  ]

  timeout = 600

  depends_on = [
    kubernetes_secret_v1.pg_conn,
    kubernetes_secret_v1.redis_conn
  ]
}


resource "kubernetes_ingress_v1" "langwatch" {
  metadata {
    name      = "langwatch"
    namespace = kubernetes_namespace_v1.langwatch.metadata[0].name

    annotations = {
      "cert-manager.io/cluster-issuer"                   = "letsencrypt-prod"
      "traefik.ingress.kubernetes.io/router.entrypoints" = "websecure"
      "traefik.ingress.kubernetes.io/router.tls"         = "true"
    }
  }

  spec {
    ingress_class_name = "traefik"

    tls {
      hosts       = [var.langwatch_fqdn]
      secret_name = "langwatch-tls"
    }

    rule {
      host = var.langwatch_fqdn

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = "langwatch-app"
              port {
                number = 5560
              }
            }
          }
        }
      }
    }
  }

  depends_on = [helm_release.langwatch]
}
