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

  # microsoft.flux cluster extension requires this RP, which is not in the
  # provider's default "core" registration set
  resource_providers_to_register = ["Microsoft.KubernetesConfiguration"]

  features {}
}
