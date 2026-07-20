data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "vault_unseal" {
  name                       = var.unseal_key_vault_name
  location                   = azurerm_resource_group.aks.location
  resource_group_name        = azurerm_resource_group.aks.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  soft_delete_retention_days = 7
}

# The applying principal needs data-plane rights to create the key when the
# Key Vault uses RBAC authorization.
resource "azurerm_role_assignment" "terraform_crypto_officer" {
  scope                = azurerm_key_vault.vault_unseal.id
  role_definition_name = "Key Vault Crypto Officer"
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
