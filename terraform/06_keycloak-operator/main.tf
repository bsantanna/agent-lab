

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

resource "null_resource" "keycloak_crds" {
  triggers = {
    version = var.keycloak_version
  }

  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${var.keycloak_version}/kubernetes/keycloaks.keycloak.org.cr.yaml
      kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${var.keycloak_version}/kubernetes/keycloakrealmimports.keycloak.org.cr.yaml
    EOT
  }

  provisioner "local-exec" {
    when = destroy
    command = <<-EOT
      kubectl delete -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${self.triggers.version}/kubernetes/keycloaks.keycloak.org.cr.yaml --ignore-not-found=true
      kubectl delete -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${self.triggers.version}/kubernetes/keycloakrealmimports.keycloak.org.cr.yaml --ignore-not-found=true
    EOT
  }
}

resource "null_resource" "wait_for_keycloak_crd" {
  triggers = {
    crds_id = null_resource.keycloak_crds.id
  }

  provisioner "local-exec" {
    command = "kubectl wait --for=condition=Established crd/keycloaks.keycloak.org --timeout=300s"
  }

  depends_on = [null_resource.keycloak_crds]
}

resource "null_resource" "keycloak_operator" {
  triggers = {
    version   = var.keycloak_version
    namespace = kubernetes_namespace_v1.keycloak.metadata[0].name
  }

  provisioner "local-exec" {
    command = <<-EOT
      kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${var.keycloak_version}/kubernetes/kubernetes.yml -n ${self.triggers.namespace}
    EOT
  }

  provisioner "local-exec" {
    when = destroy
    command = <<-EOT
      kubectl delete -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/${self.triggers.version}/kubernetes/kubernetes.yml -n ${self.triggers.namespace} --ignore-not-found=true
    EOT
  }

  depends_on = [null_resource.wait_for_keycloak_crd]
}
