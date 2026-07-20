output "resource_group_name" {
  value = azurerm_resource_group.aks.name
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.this.name
}

output "unseal_key_vault_name" {
  value = azurerm_key_vault.vault_unseal.name
}

output "unseal_key_name" {
  value = azurerm_key_vault_key.vault_unseal.name
}

output "get_credentials_command" {
  description = "Run this to configure kubectl for the cluster"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.aks.name} --name ${azurerm_kubernetes_cluster.this.name} --overwrite-existing"
}
