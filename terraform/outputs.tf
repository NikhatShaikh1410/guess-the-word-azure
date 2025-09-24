output "container_app_url" {
  value       = "https://${azurerm_container_app.main.latest_revision_fqdn}"
  description = "The FQDN of the deployed web application."
}