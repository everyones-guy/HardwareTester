locals {
  name_prefix = "${var.project}-${var.env}"
  tags = {
    project = var.project
    env     = var.env
    managed = "terraform"
  }
}