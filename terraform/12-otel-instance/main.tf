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

resource "kubernetes_namespace_v1" "otel" {
  metadata {
    name = "otel"
  }
}

resource "helm_release" "otel_collector" {
  name       = "otel-collector"
  repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart      = "opentelemetry-collector"
  namespace  = kubernetes_namespace_v1.otel.metadata[0].name

  values = [
    yamlencode({
      mode = "deployment"
      image = {
        repository = "otel/opentelemetry-collector-contrib"
        tag        = "latest"
      }
      config = {
        receivers = {
          otlp = {
            protocols = {
              http = {
                endpoint = "0.0.0.0:4318"
              }
            }
          }
        }
        exporters = {
          otlphttp: {
            endpoint = var.otlp_http_endpoint
            headers = {
              "Authorization" = "Bearer ${var.otlp_http_auth_token}"
            }
            tls = {
              insecure_skip_verify = true
            }
          }
        }
        service = {
          pipelines = {
            traces = {
              receivers  = ["otlp"]
              exporters  = ["otlphttp"]
            }
            metrics = {
              receivers  = ["otlp"]
              exporters  = ["otlphttp"]
            }
            logs = {
              receivers  = ["otlp"]
              exporters  = ["otlphttp"]
            }
          }
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.otel]
}
