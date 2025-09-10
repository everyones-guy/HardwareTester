module "core" {
  source   = "./modules/core"
  location = var.location
  name     = local.name_prefix
  tags     = local.tags
}

module "logging" {
  source   = "./modules/logging"
  rg_name  = module.core.rg_name
  location = var.location
  name     = local.name_prefix
  tags     = local.tags
}

module "registry" {
  source   = "./modules/registry"
  rg_name  = module.core.rg_name
  location = var.location
  name     = local.name_prefix
  sku      = var.acr_sku
  tags     = local.tags
}

module "keyvault" {
  source   = "./modules/keyvault"
  rg_name  = module.core.rg_name
  location = var.location
  name     = local.name_prefix
  tags     = local.tags
}

module "storage" {
  source   = "./modules/storage"
  rg_name  = module.core.rg_name
  location = var.location
  name     = local.name_prefix
  tags     = local.tags
}

module "containerapps" {
  source                 = "./modules/containerapps"
  rg_name                = module.core.rg_name
  location               = var.location
  name                   = local.name_prefix
  log_analytics_id       = module.logging.log_analytics_id
  log_analytics_key      = module.logging.log_analytics_key
  acr_id                 = module.registry.acr_id
  acr_server             = module.registry.acr_server
  key_vault_id           = module.keyvault.kv_id
  storage_account_name   = module.storage.sa_name

  uht_backend_image      = var.uht_backend_image
  uht_frontend_image     = var.uht_frontend_image

  backend_cpu            = var.backend_cpu
  backend_memory         = var.backend_memory
  backend_target_port    = var.backend_target_port

  frontend_cpu           = var.frontend_cpu
  frontend_memory        = var.frontend_memory
  frontend_target_port   = var.frontend_target_port

  tags = local.tags
}