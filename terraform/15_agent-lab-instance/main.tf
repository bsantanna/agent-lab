
terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = ">= 3.0.0"
    }
  }
}

provider "helm" {
  kubernetes = {
    config_path = "~/.kube/config"
  }
}

resource "helm_release" "agent_lab" {
  name       = "agent-lab"
  repository = "https://bsantanna.github.io/agent-lab"
  chart      = "agent-lab"
  version    = var.agent_lab_chart_version
  namespace  = var.agent_lab_namespace

  values = [
    yamlencode({
      config = {
        telemetry_endpoint = var.telemetry_endpoint
      }

      ingress = {
        enabled = true
        className = "traefik"
        hosts = [{
          host = var.agent_lab_fqdn
          paths = [{
            path     = "/"
            pathType = "Prefix"
          }]
        }]
        tls = [{
          hosts      = [var.agent_lab_fqdn]
          secretName = "agent-lab-tls"
        }]
        annotations = {
          "cert-manager.io/cluster-issuer" = "letsencrypt-prod"
        }
      }

      livenessProbe = {
        timeoutSeconds = 60
      }

      readinessProbe = {
        timeoutSeconds = 60
      }

      image = {
        tag = var.agent_lab_image_tag
      }
    })
  ]
}
