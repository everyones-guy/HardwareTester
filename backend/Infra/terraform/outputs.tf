output "resource_group" { value = module.core.rg_name }
output "acr_server"     { value = module.registry.acr_server }
output "frontend_url"   { value = module.containerapps.frontend_fqdn }
output "backend_url"    { value = module.containerapps.backend_fqdn }
output "storage_account"{ value = module.storage.sa_name }
output "key_vault"      { value = module.keyvault.kv_name }