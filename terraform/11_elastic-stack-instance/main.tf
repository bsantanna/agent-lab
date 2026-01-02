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

resource "kubernetes_namespace_v1" "elastic" {
  metadata {
    name = "elastic"
  }
}

# ServersTransport for Elasticsearch backend (HTTPS with skip verify)
resource "kubernetes_manifest" "es_servers_transport" {
  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "ServersTransport"

    metadata = {
      name      = "es-backend-tls"
      namespace = kubernetes_namespace_v1.elastic.metadata[0].name
    }

    spec = {
      insecureSkipVerify = true
    }
  }

  depends_on = [kubernetes_namespace_v1.elastic]
}

# ServersTransport for Kibana backend (HTTPS with skip verify)
resource "kubernetes_manifest" "kb_servers_transport" {
  manifest = {
    apiVersion = "traefik.io/v1alpha1"
    kind       = "ServersTransport"

    metadata = {
      name      = "kb-backend-tls"
      namespace = kubernetes_namespace_v1.elastic.metadata[0].name
    }

    spec = {
      insecureSkipVerify = true
    }
  }

  depends_on = [kubernetes_namespace_v1.elastic]
}

resource "helm_release" "elastic" {
  name       = "elastic"
  repository = "https://helm.elastic.co"
  chart      = "eck-stack"
  namespace  = kubernetes_namespace_v1.elastic.metadata[0].name

  values = [
    yamlencode({
      eck-elasticsearch = {
        enabled          = true
        fullnameOverride = "elasticsearch"

        http = {
          tls = {
            selfSignedCertificate = {
              disabled = false
            }
          }
        }

        ingress = {
          enabled = false  # Disable built-in ingress; use custom below
        }
      }

      eck-kibana = {
        enabled          = true
        fullnameOverride = "kibana"

        config = {
          xpack = {
            fleet = {
              packages = [
                {
                  name    = "apm"
                  version = "latest"
                }
              ]
            }
          }
        }

        http = {
          tls = {
            selfSignedCertificate = {
              disabled = false
            }
          }
        }

        ingress = {
          enabled = false  # Disable built-in ingress; use custom below
        }
      }

      eck-apm-server = {
        enabled = true

        elasticsearchRef = {
          name = "elasticsearch"
        }

        kibanaRef = {
          name = "kibana"
        }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.elastic,
    kubernetes_manifest.es_servers_transport,
    kubernetes_manifest.kb_servers_transport
  ]
}

# Custom Traefik Ingress for Elasticsearch
resource "kubernetes_ingress_v1" "elasticsearch" {
  metadata {
    name      = "elasticsearch"
    namespace = kubernetes_namespace_v1.elastic.metadata[0].name

    annotations = {
      "cert-manager.io/cluster-issuer"                          = "letsencrypt-prod"
      "traefik.ingress.kubernetes.io/router.entrypoints"        = "websecure"
      "traefik.ingress.kubernetes.io/router.tls"                = "true"
      "traefik.ingress.kubernetes.io/service.serversscheme"     = "https"
      "traefik.ingress.kubernetes.io/service.serverstransport"  = kubernetes_manifest.es_servers_transport.manifest.metadata.name
    }
  }

  spec {
    ingress_class_name = "traefik"

    tls {
      hosts       = [var.elasticsearch_fqdn]
      secret_name = "elasticsearch-tls"
    }

    rule {
      host = var.elasticsearch_fqdn

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = "elasticsearch-es-http"
              port {
                number = 9200
              }
            }
          }
        }
      }
    }
  }

  depends_on = [helm_release.elastic]
}

# Custom Traefik Ingress for Kibana
resource "kubernetes_ingress_v1" "kibana" {
  metadata {
    name      = "kibana"
    namespace = kubernetes_namespace_v1.elastic.metadata[0].name

    annotations = {
      "cert-manager.io/cluster-issuer"                          = "letsencrypt-prod"
      "traefik.ingress.kubernetes.io/router.entrypoints"        = "websecure"
      "traefik.ingress.kubernetes.io/router.tls"                = "true"
      "traefik.ingress.kubernetes.io/service.serversscheme"     = "https"
      "traefik.ingress.kubernetes.io/service.serverstransport"  = kubernetes_manifest.kb_servers_transport.manifest.metadata.name
    }
  }

  spec {
    ingress_class_name = "traefik"

    tls {
      hosts       = [var.kibana_fqdn]
      secret_name = "kibana-tls"
    }

    rule {
      host = var.kibana_fqdn

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = "kibana-kb-http"
              port {
                number = 5601
              }
            }
          }
        }
      }
    }
  }

  depends_on = [helm_release.elastic]
}
