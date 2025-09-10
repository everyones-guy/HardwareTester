variable "rg_name"              { type = string }
variable "location"             { type = string }
variable "name"                 { type = string }
variable "log_analytics_id"     { type = string }
variable "log_analytics_key"    { type = string }
variable "acr_id"               { type = string }
variable "acr_server"           { type = string }
variable "key_vault_id"         { type = string }
variable "storage_account_name" { type = string }

variable "uht_backend_image"  { type = string }
variable "uht_frontend_image" { type = string }

variable "backend_cpu"       { type = number }
variable "backend_memory"    { type = string }
variable "backend_target_port"{ type = number }
variable "frontend_cpu"      { type = number }
variable "frontend_memory"   { type = string }
variable "frontend_target_port"{ type = number }

variable "tags" { type = map(string) }