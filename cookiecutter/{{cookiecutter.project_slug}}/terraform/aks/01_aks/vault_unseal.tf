data "azurerm_client_config" "current" {}

# A prior cluster whose resource group was deleted out of band (or whose state
# was lost) leaves this vault soft-deleted, not gone. With recover disabled the
# vault create would fail on the leftover; purge any soft-deleted remnant of
# this name first so every apply starts from nothing. No-op on a first-ever
# apply and on normal re-applies: triggers_replace keeps this from re-running
# while the name is unchanged, so it never touches a live vault.
resource "terraform_data" "purge_stale_unseal_vault" {
  triggers_replace = {
    name = var.unseal_key_vault_name
  }

  provisioner "local-exec" {
    interpreter = ["/bin/sh", "-c"]

    environment = {
      KV  = var.unseal_key_vault_name
      LOC = var.location
    }

    command = <<-EOT
      set -eu
      if [ -n "$(az keyvault list-deleted --query "[?name=='$KV'] | [0].name" -o tsv 2>/dev/null)" ]; then
        echo "purging soft-deleted key vault '$KV' left over from a prior cluster..."
        az keyvault purge --name "$KV" --location "$LOC"
      else
        echo "no soft-deleted key vault '$KV' to purge."
      fi
    EOT
  }
}

resource "azurerm_key_vault" "vault_unseal" {
  name                       = var.unseal_key_vault_name
  location                   = azurerm_resource_group.aks.location
  resource_group_name        = azurerm_resource_group.aks.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  soft_delete_retention_days = 7

  depends_on = [terraform_data.purge_stale_unseal_vault]
}

# The applying principal needs data-plane rights to create the key when the
# Key Vault uses RBAC authorization.
resource "azurerm_role_assignment" "terraform_crypto_officer" {
  scope                = azurerm_key_vault.vault_unseal.id
  role_definition_name = "Key Vault Crypto Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# 03_vault_config stores the Vault root token + recovery keys here during its
# init step and reads the root token back; both need data-plane secret rights.
resource "azurerm_role_assignment" "terraform_secrets_officer" {
  scope                = azurerm_key_vault.vault_unseal.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_key_vault_key" "vault_unseal" {
  name         = var.unseal_key_name
  key_vault_id = azurerm_key_vault.vault_unseal.id
  key_type     = "RSA"
  key_size     = 2048
  key_opts     = ["unwrapKey", "wrapKey"]

  depends_on = [azurerm_role_assignment.terraform_crypto_officer]
}

# Vault's azurekeyvault seal authenticates via IMDS as the kubelet identity;
# this role allows get/wrap/unwrap on the unseal key.
resource "azurerm_role_assignment" "kubelet_unseal" {
  scope                = azurerm_key_vault.vault_unseal.id
  role_definition_name = "Key Vault Crypto Service Encryption User"
  principal_id         = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
}
