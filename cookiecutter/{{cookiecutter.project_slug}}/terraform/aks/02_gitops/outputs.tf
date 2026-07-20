output "flux_configuration_name" {
  value = azurerm_kubernetes_flux_configuration.this.name
}

output "check_sync_status_command" {
  description = "Run this to inspect Flux reconciliation status"
  value       = "az k8s-configuration flux show --resource-group ${var.resource_group_name} --cluster-name ${var.cluster_name} --cluster-type managedClusters --name ${azurerm_kubernetes_flux_configuration.this.name}"
}

output "get_traefik_ip_command" {
  description = "Run this once traefik is up to read the LoadBalancer public IP; point the vault/app hostnames at it before applying 03_vault_config"
  value       = "kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
}
