terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "UHTtfadmin"
    container_name       = "tfstate"
    key                  = "uht/dev.tfstate"
  }
}