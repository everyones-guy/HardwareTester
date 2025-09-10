resource "azurerm_key_vault" "kv" {
  name                        = replace("${var.name}-kv", "_", "-")
  location                    = var.location
  resource_group_name         = var.rg_name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  purge_protection_enabled    = true
  soft_delete_retention_days  = 7
  public_network_access_enabled = true
  tags                        = var.tags
}

data "azurerm_client_config" "current" {}