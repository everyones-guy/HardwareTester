# UHT Terraform Stack (Azure)

## Prereqs
- Azure CLI logged in (`az login`) & correct subscription selected
- Terraform >= 1.6
- An Azure Storage Account/Container for remote state

## 1) Backend bootstrap (one-time)
# Choose globally-unique storage account name
az group create -n tfstate-rg -l centralus
az storage account create -n <YOUR_TFSTATE_SA> -g tfstate-rg -l centralus --sku Standard_LRS
az storage container create --name tfstate --account-name <YOUR_TFSTATE_SA>

## 2) Configure env backend
Edit `envs/dev/backend.tf` (and prod) to point at your tfstate RG/SA/container.

## 3) Build & push images to ACR
# create ACR or use the one Terraform will create (after first apply)
az acr build -r <acrName> -t uht-backend:latest -f ../../Dockerfile ../../
az acr build -r <acrName> -t uht-frontend:latest -f ../../Dockerfile-frontend ../../

## 4) Plan/Apply
cd envs/dev
cp ../../terraform.tfvars.example ./terraform.tfvars
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars

## 5) Outputs
`frontend_url` and `backend_url` will show the public FQDNs.