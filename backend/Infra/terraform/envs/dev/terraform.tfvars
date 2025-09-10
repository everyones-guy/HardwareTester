subscription_id    = "00000000-0000-0000-0000-000000000000"
tenant_id          = "00000000-0000-0000-0000-000000000000"
location           = "centralus"
project            = "uht"
env                = "dev"

# After you build & push to ACR (see README), set these to your images
uht_backend_image  = "uhtacr.azurecr.io/uht-backend:latest"
uht_frontend_image = "uhtacr.azurecr.io/uht-frontend:latest"