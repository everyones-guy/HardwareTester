output "log_analytics_id"  { value = azurerm_log_analytics_workspace.law.id }
output "log_analytics_key" { value = azurerm_log_analytics_workspace.law.primary_shared_key }