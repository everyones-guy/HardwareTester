variable "subscription_id" { type = string }
variable "tenant_id"       { type = string }

variable "location" {
  type    = string
  default = "centralus"
}

variable "project" {
  type    = string
  default = "uht"
}

variable "env" {
  type    = string
  default = "dev"
}

variable "acr_sku" {
  type    = string
  default = "Basic"
}

# Container images (ACR or Docker Hub). Example: uhtacr.azurecr.io/uht-backend:latest
variable "uht_backend_image" { type = string }
variable "uht_frontend_image" { type = string }

# Container sizing
variable "backend_cpu"    { type = number, default = 0.5 }
variable "backend_memory" { type = string, default = "1.0Gi" }
variable "frontend_cpu"   { type = number, default = 0.5 }
variable "frontend_memory"{ type = string, default = "0.5Gi" }

# Frontend ingress
variable "frontend_target_port" { type = number, default = 80 }
variable "backend_target_port"  { type = number, default = 5000 }

# Optional custom domain (leave blank to skip)
variable "custom_domain" { type = string, default = "" }