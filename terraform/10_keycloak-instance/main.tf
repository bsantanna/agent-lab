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

resource "helm_release" "pg_keycloak" {
  name       = "pg-keycloak"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = "keycloak"

  values = [
    yamlencode({
      cluster = {
        imageName = var.pg_vector_image
        instances = 1
        storage = {
          size = "1Gi"
        }
      }
    })
  ]
}

data "kubernetes_secret_v1" "pg_app_secret" {
  metadata {
    name      = "${helm_release.pg_keycloak.name}-cluster-app"
    namespace = helm_release.pg_keycloak.namespace
  }

  depends_on = [helm_release.pg_keycloak]
}

resource "kubernetes_manifest" "keycloak_instance" {
  manifest = {
    apiVersion = "k8s.keycloak.org/v2alpha1"
    kind       = "Keycloak"

    metadata = {
      name      = "keycloak"
      namespace = "keycloak"
    }

    spec = {
      image = var.keycloak_image

      instances = 1

      db = {
        vendor   = "postgres"
        host     = "${helm_release.pg_keycloak.name}-cluster-rw.keycloak.svc.cluster.local"
        port     = 5432
        database = "app"

        usernameSecret = {
          name = data.kubernetes_secret_v1.pg_app_secret.metadata[0].name
          key  = "username"
        }

        passwordSecret = {
          name = data.kubernetes_secret_v1.pg_app_secret.metadata[0].name
          key  = "password"
        }
      }

      http = {
        httpEnabled = true
      }

      hostname = {
        hostname = var.keycloak_hostname
      }

      proxy = {
        headers = "xforwarded"
      }

      ingress = {
        enabled = false
      }
    }
  }

  depends_on = [
    data.kubernetes_secret_v1.pg_app_secret
  ]
}


resource "kubernetes_ingress_v1" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = "keycloak"

    annotations = {
      "cert-manager.io/cluster-issuer"                   = "letsencrypt-prod"
      "traefik.ingress.kubernetes.io/router.entrypoints" = "websecure"
      "traefik.ingress.kubernetes.io/router.tls"         = "true"
    }
  }

  spec {
    ingress_class_name = "traefik"

    tls {
      hosts       = [var.keycloak_hostname]
      secret_name = "keycloak-tls"
    }

    rule {
      host = var.keycloak_hostname

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = "keycloak-service"
              port {
                number = 8080
              }
            }
          }
        }
      }
    }
  }

  depends_on = [kubernetes_manifest.keycloak_instance]
}
