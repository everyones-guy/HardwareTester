resource "azurerm_container_registry" "acr" {
  name                = replace("${var.name}acr", "-", "")
  resource_group_name = var.rg_name
  location            = var.location
  sku                 = var.sku
  admin_enabled       = false
  tags                = var.tags
}