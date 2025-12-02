# Terraform Starter (AWS)

## Local usage
1) Python helper
   python3 scripts/tfctl.py scaffold
   terraform -chdir=terraform init \
     -backend-config="bucket=my-tf-state-bucket" \
     -backend-config="key=envs/dev/terraform.tfstate" \
     -backend-config="region=us-east-1" \
     -backend-config="dynamodb_table=tf-state-lock"

2) Plan/Apply with vars
   python3 scripts/tfctl.py plan   -var "project_name=uht-demo"
   python3 scripts/tfctl.py apply  -var "project_name=uht-demo"
   python3 scripts/tfctl.py destroy -var "project_name=uht-demo"

## Docker usage
# Build and run in a clean container
docker build -t tfctl .
docker run --rm -it \
  -e AWS_PROFILE=default \
  -v $HOME/.aws:/root/.aws:ro \
  -v $(pwd)/terraform:/app/terraform \
  tfctl scaffold
# Then:
docker run --rm -it -e AWS_PROFILE=default -v $HOME/.aws:/root/.aws:ro -v $(pwd)/terraform:/app/terraform tfctl init
docker run --rm -it -e AWS_PROFILE=default -v $HOME/.aws:/root/.aws:ro -v $(pwd)/terraform:/app/terraform tfctl plan -var "project_name=uht-demo"

## Kubernetes usage (EKS + IRSA)
kubectl apply -f k8s/terraform-job.yaml

## AWS auth options
- Env vars: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
- Profile: export AWS_PROFILE=your-profile
- EKS (IRSA): service account mapped to an IAM role

## Common Terraform commands
terraform fmt                   # format code
terraform validate              # static validation
terraform state list            # what’s managed
terraform state show <addr>     # inspect a resource in state
terraform workspace list        # environments
terraform taint/untaint         # force replace a resource (rarely needed)


---

## Folder Tree

```
infra/terraform/
   envs/
      dev/
         backend.tf                # remote state (edit the names)
         terraform.tfvars          # your dev values
         README.md
      prod/
         backend.tf
         terraform.tfvars
         README.md
   modules/
      core/                         # RG + tags
         main.tf
         variables.tf
         outputs.tf
      logging/                      # Log Analytics
         main.tf
         variables.tf
         outputs.tf
      registry/                     # ACR + RBAC hookup
         main.tf
         variables.tf
         outputs.tf
      keyvault/                     # Key Vault + access policy
         main.tf
         variables.tf
         outputs.tf
      storage/                      # Blob storage for snapshots/logs
         main.tf
         variables.tf
         outputs.tf
      containerapps/                # Env + Apps (frontend/backend)
         main.tf
         variables.tf
         outputs.tf
   versions.tf                      # TF & provider versions
   providers.tf                     # azurerm provider
   variables.tf                     # global vars
   locals.tf                        # naming & tags
   main.tf                          # wire modules together
   outputs.tf
   terraform.tfvars.example         # copy into envs/<env>/terraform.tfvars
   README.md                        # usage
```

---

## Quick Commands

```bash
# From infra/terraform/envs/dev
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars -auto-approve
terraform output
```

## Image Build (after first apply creates ACR)

```bash
ACR_NAME=$(terraform output -raw acr_server | cut -d'.' -f1)
# backend
az acr build -r $ACR_NAME -t uht-backend:latest -f ../../../Dockerfile ../../../
# frontend (create a Dockerfile-frontend or point at your existing one)
az acr build -r $ACR_NAME -t uht-frontend:latest -f ../../../Dockerfile-frontend ../../../
```
