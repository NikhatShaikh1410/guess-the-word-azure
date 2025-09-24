# --- Provider & Backend Configuration ---
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  # NOTE: The backend block is commented out for initial local runs.
  # The CI/CD pipeline will uncomment and configure this.
  /*
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "sttfstateguessword" # MUST BE GLOBALLY UNIQUE
    container_name       = "tfstate"
    key                  = "wordgame.tfstate"
  }
  */
}

provider "azurerm" {
  features {}
}

# --- Data & Locals ---
data "azurerm_client_config" "current" {}

locals {
  # Use terraform workspace to create unique names for staging vs. production
  env_suffix = terraform.workspace == "default" ? "staging" : terraform.workspace
  tags = {
    environment = local.env_suffix
    project     = "WordGame"
  }
}

# --- Resource Group ---
resource "azurerm_resource_group" "main" {
  name     = "${var.resource_group_name_prefix}-${local.env_suffix}"
  location = var.location
  tags     = local.tags
}

# --- Container Registry (ACR) ---
# We create one ACR and share it between staging and prod
resource "azurerm_container_registry" "main" {
  name                = "${var.acr_name}${local.env_suffix}" # Unique name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false # Use identity-based access
}

# --- PostgreSQL Flexible Server ---
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.postgres_server_name}-${local.env_suffix}"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "15"
  sku_name               = "B_Standard_B1ms" # Smallest SKU for demo
  administrator_login    = "psqladmin"       # An admin login is required but we won't use its password
  administrator_password = "a-placeholder-password-that-is-not-used"
  storage_mb             = 32768
  zone                   = "1"

  # Enable Azure AD Authentication
  authentication {
    active_directory_auth_enabled = true
    password_auth_enabled         = false # Disable password auth for security
    tenant_id                     = data.azurerm_client_config.current.tenant_id
  }

  tags = local.tags
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.postgres_db_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# --- Container App Environment ---
resource "azurerm_container_app_environment" "main" {
  name                = "cae-wordgame-${local.env_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.tags
}

# --- Container App ---
resource "azurerm_container_app" "main" {
  name                         = "${var.container_app_name}-${local.env_suffix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  # --- Managed Identity for Passwordless DB Access ---
  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name   = "wordgame-app"
      image  = "${azurerm_container_registry.main.login_server}/${var.container_app_name}:${var.docker_image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"

      env = [
        { name = "SECRET_KEY", value = "a-production-secret-key" },
        { name = "DB_HOST", value = azurerm_postgresql_flexible_server.main.name },
        { name = "DB_NAME", value = azurerm_postgresql_flexible_server_database.main.name },
        # The user MUST be the name of the Container App for AAD auth
        { name = "DB_USER", value = azurerm_container_app.main.name },
        # Note: DB_PASS is intentionally not set
        { name = "DB_PORT", value = "5432" },
        # This is used by DefaultAzureCredential
        { name = "AZURE_CLIENT_ID", value = self.identity[0].principal_id },
      ]
    }
  }

  ingress {
    external_enabled = true
    target_port      = 5000 # The port gunicorn is running on
    transport        = "http"
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = self.identity[0].identity_id
  }

  tags = local.tags
}

# --- IAM Role Assignment for Passwordless DB Access ---
# Give the Container App's Managed Identity permission to act as a user on the PostgreSQL server.
resource "azurerm_role_assignment" "db_user_role" {
  scope                = azurerm_postgresql_flexible_server.main.id
  role_definition_name = "Azure Database for PostgreSQL User"
  principal_id         = azurerm_container_app.main.identity[0].principal_id
}

# Grant the Container App's identity AcrPull role on the registry
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.main.identity[0].principal_id
}