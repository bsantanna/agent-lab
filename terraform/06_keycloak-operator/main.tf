

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

resource "null_resource" "keycloak_operator" {
  triggers = {
    version   = var.keycloak_version
    namespace = kubernetes_namespace_v1.keycloak.metadata[0].name
  }

  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${self.triggers.version}/kubernetes/kubernetes.yml -n ${self.triggers.namespace}
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      kubectl delete -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${self.triggers.version}/kubernetes/kubernetes.yml -n ${self.triggers.namespace} --ignore-not-found=true
    EOT
  }

  depends_on = [kubernetes_namespace_v1.keycloak]
}


# resource "kubernetes_manifest" "keycloak_instance" {
#   manifest = {
#     apiVersion = "k8s.keycloak.org/v2alpha1"
#     kind       = "Keycloak"
#
#     metadata = {
#       name      = "keycloak"
#       namespace = kubernetes_namespace_v1.keycloak.metadata[0].name
#     }
#
#     spec = {
#       image = "quay.io/keycloak/keycloak:${var.keycloak_version}"
#       instances = 1
#
#       db = {
#         vendor   = "postgres"
#         host     = "${helm_release.pg_keycloak.name}-cluster-rw.${kubernetes_namespace_v1.keycloak.metadata[0].name}.svc.cluster.local"
#         database = "app"  # Matches default CNPG app database
#
#         usernameSecret = {
#           name = data.kubernetes_secret_v1.pg_app_secret.metadata[0].name
#           key  = "username"
#         }
#
#         passwordSecret = {
#           name = data.kubernetes_secret_v1.pg_app_secret.metadata[0].name
#           key  = "password"
#         }
#       }
#
#       hostname = {
#         hostname = var.keycloak_hostname
#       }
#
#       http = {
#         httpEnabled = true
#       }
#
#       proxy = {
#         headers = "xforwarded"  # Traefik sends X-Forwarded-* headers
#       }
#
#       ingress = {
#         enabled = false  # We manage our own Ingress for full Traefik/cert-manager control
#       }
#     }
#   }
#
#   depends_on = [
#     null_resource.keycloak_operator,
#     data.kubernetes_secret_v1.pg_app_secret
#   ]
# }
#
#
# # Custom Ingress (Traefik + cert-manager) pointing to the operator-created HTTP service
# resource "kubernetes_ingress_v1" "keycloak" {
#   metadata {
#     name      = "keycloak"
#     namespace = kubernetes_namespace_v1.keycloak.metadata[0].name
#     annotations = {
#       "cert-manager.io/cluster-issuer"                   = "letsencrypt-prod"
#       "traefik.ingress.kubernetes.io/router.entrypoints" = "websecure"
#       "traefik.ingress.kubernetes.io/router.tls"         = "true"
#     }
#   }
#
#   spec {
#     ingress_class_name = "traefik"
#
#     rule {
#       host = var.keycloak_hostname
#       http {
#         path {
#           path      = "/"
#           path_type = "Prefix"
#           backend {
#             service {
#               name = "keycloak-service"  # Operator-created service name: <CR name>-service
#               port {
#                 number = 80  # HTTP port (httpEnabled: true)
#               }
#             }
#           }
#         }
#       }
#     }
#
#     tls {
#       hosts = [var.keycloak_hostname]
#     }
#   }
#
#   depends_on = [kubernetes_manifest.keycloak_instance]
# }
