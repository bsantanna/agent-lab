output "get_root_token_command" {
  description = "Retrieve the Vault root token from Key Vault for manual vault CLI access (this stage reads it automatically)"
  value       = "az keyvault secret show --vault-name ${var.unseal_key_vault_name} --name ${var.init_secret_name} --query value -o tsv | jq -r .root_token"
}
