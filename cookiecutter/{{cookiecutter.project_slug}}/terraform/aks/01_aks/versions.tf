terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  subscription_id = var.subscription_id

  features {
    key_vault {
      # terraform destroy purges the vault + unseal key instead of leaving them
      # soft-deleted, so a recreate starts clean. Recover is disabled so a stale
      # soft-deleted remnant fails loudly rather than silently dragging an old
      # active key back into the recovered vault (which is what broke the key
      # create). terraform_data.purge_stale_unseal_vault clears such remnants
      # before the vault is created.
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = false
    }
  }
}
