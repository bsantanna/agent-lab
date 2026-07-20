data "azurerm_client_config" "current" {}

data "azurerm_kubernetes_cluster" "this" {
  name                = var.cluster_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_kubernetes_cluster_extension" "flux" {
  name           = "flux"
  cluster_id     = data.azurerm_kubernetes_cluster.this.id
  extension_type = "microsoft.flux"

  configuration_settings = {
    "multiTenancy.enforce" = "false"
  }
}

resource "azurerm_kubernetes_flux_configuration" "this" {
  name       = var.flux_configuration_name
  cluster_id = data.azurerm_kubernetes_cluster.this.id
  namespace  = var.flux_namespace
  scope      = "cluster"

  git_repository {
    url              = var.git_repository_url
    reference_type   = "branch"
    reference_value  = var.git_branch
    https_user       = var.github_user
    https_key_base64 = base64encode(var.github_pat)
  }

  kustomizations {
    name                       = "infra-controllers"
    path                       = "${var.gitops_path}/infrastructure/controllers"
    garbage_collection_enabled = true
    wait                       = true
  }

  kustomizations {
    name                       = "infra-configs"
    path                       = "${var.gitops_path}/infrastructure/configs"
    garbage_collection_enabled = true
    wait                       = true
    depends_on                 = ["infra-controllers"]

    post_build {
      substitute = {
        cert_manager_email = var.cert_manager_email
        vault_hostname     = var.vault_hostname
        pg_image           = var.pg_image
        # azurekeyvault seal for Vault auto-unseal (key managed by 01_aks);
        # the seal authenticates via IMDS as the kubelet identity
        azure_tenant_id       = data.azurerm_client_config.current.tenant_id
        unseal_client_id      = data.azurerm_kubernetes_cluster.this.kubelet_identity[0].client_id
        unseal_key_vault_name = var.unseal_key_vault_name
        unseal_key_name       = var.unseal_key_name
      }
    }
  }

  kustomizations {
    name                       = var.kustomization_name
    path                       = "${var.gitops_path}/apps"
    garbage_collection_enabled = true
    depends_on                 = ["infra-configs"]

    post_build {
      substitute = {
        app_hostname = var.app_hostname
      }
    }
  }

  depends_on = [azurerm_kubernetes_cluster_extension.flux]
}
