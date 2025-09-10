output "env_id"          { value = azurerm_container_app_environment.env.id }
output "frontend_fqdn"   { value = azurerm_container_app.frontend.latest_revision_fqdn }
output "backend_fqdn"    { value = azurerm_container_app.backend.latest_revision_fqdn }
output "apps_identity_id"{ value = azurerm_user_assigned_identity.apps.id }