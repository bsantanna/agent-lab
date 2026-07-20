output "flux_configuration_name" {
  value = azurerm_kubernetes_flux_configuration.this.name
}

output "check_sync_status_command" {
  description = "Run this to inspect Flux reconciliation status"
  value       = "az k8s-configuration flux show --resource-group ${var.resource_group_name} --cluster-name ${var.cluster_name} --cluster-type managedClusters --name ${azurerm_kubernetes_flux_configuration.this.name}"
}
