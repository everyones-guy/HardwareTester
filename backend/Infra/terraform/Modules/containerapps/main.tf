# User-assigned identity for pulling from ACR and accessing Key Vault
resource "azurerm_user_assigned_identity" "apps" {
  name                = "${var.name}-apps-mi"
  location            = var.location
  resource_group_name = var.rg_name
  tags                = var.tags
}

# Allow MI to pull from ACR
resource "azurerm_role_assignment" "acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.apps.principal_id
}

# Allow MI to read secrets from Key Vault
resource "azurerm_role_assignment" "kv_secrets_user" {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.apps.principal_id
}

resource "azurerm_container_app_environment" "env" {
  name                       = "${var.name}-cae"
  location                   = var.location
  resource_group_name        = var.rg_name
  log_analytics_workspace_id = var.log_analytics_id
  infrastructure_subnet_id   = null
  tags                       = var.tags
}

# Backend app
resource "azurerm_container_app" "backend" {
  name                         = "${var.name}-backend"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = var.rg_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.apps.id]
  }

  registry {
    server   = var.acr_server
    identity = azurerm_user_assigned_identity.apps.id
  }

  template {
    container {
      name   = "backend"
      image  = var.uht_backend_image
      cpu    = var.backend_cpu
      memory = var.backend_memory

      env {
        name  = "STORAGE_ACCOUNT"
        value = var.storage_account_name
      }
      # Example: read secret from Key Vault via Dapr/Env — for simplicity we define plain env
      # You can mount Managed Identity into app and fetch at runtime.
    }
    http_scale_rule { # minimal autoscale example
      name = "default"
      http {
        concurrent_requests = 50
      }
      min_replicas = 1
      max_replicas = 3
    }
  }

  ingress {
    external_enabled = true
    target_port      = var.backend_target_port
    transport        = "auto"
  }
}

# Frontend app
resource "azurerm_container_app" "frontend" {
  name                         = "${var.name}-frontend"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = var.rg_name
  revision_mode                = "Single"
  tags                         = var.tags

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.apps.id]
  }

  registry {
    server   = var.acr_server
    identity = azurerm_user_assigned_identity.apps.id
  }

  template {
    container {
      name   = "frontend"
      image  = var.uht_frontend_image
      cpu    = var.frontend_cpu
      memory = var.frontend_memory

      env { name = "VITE_API_BASE_URL" value = azurerm_container_app.backend.latest_revision_fqdn }
    }
    http_scale_rule {
      name = "default"
      http { concurrent_requests = 80 }
      min_replicas = 1
      max_replicas = 3
    }
  }

  ingress {
    external_enabled = true
    target_port      = var.frontend_target_port
    transport        = "auto"
  }
}