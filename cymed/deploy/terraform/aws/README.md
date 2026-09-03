# CyMed on AWS — Terraform

Baseline account infrastructure: VPC (3 AZs), EKS, RDS Postgres 16 Multi-AZ,
ElastiCache Redis, ALB, KMS CMKs (one per data class), and an S3 artefact
bucket. Everything else (application, ingress-nginx, cert-manager, sealed-
secrets, workloads) is applied on top with `kubectl kustomize` from
`deploy/k8s/overlays/<env>`.

## Prerequisites

- Terraform >= 1.6.0
- AWS credentials in the target account (SSO profile, `aws-vault`, or CI role)
- `kubectl` >= 1.28 for post-apply verification
- Optional but recommended: `tflint`, `checkov`, `terraform-docs`

## First-time init — remote state

Create the state bucket and DynamoDB lock table once per AWS account:

```bash
# In the target account, region us-east-1:
aws s3api create-bucket \
  --bucket cymed-tfstate-$(aws sts get-caller-identity --query Account --output text) \
  --region us-east-1

aws s3api put-bucket-versioning \
  --bucket cymed-tfstate-<account-id> \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket cymed-tfstate-<account-id> \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

aws dynamodb create-table \
  --table-name cymed-tf-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

Then uncomment the `backend "s3"` block in `versions.tf` and run:

```bash
terraform init -reconfigure
```

## Workspace per environment

Keep dev / staging / prod state files distinct via Terraform workspaces:

```bash
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# select the target env before plan/apply
terraform workspace select prod
```

Interpolate the workspace into the state key so each has its own file:

```hcl
# versions.tf backend block
backend "s3" {
  bucket         = "cymed-tfstate-<account-id>"
  key            = "aws/${terraform.workspace}/terraform.tfstate"
  region         = "us-east-1"
  dynamodb_table = "cymed-tf-locks"
  encrypt        = true
}
```

## Plan / apply

```bash
terraform plan  -var-file=envs/prod.tfvars -out=plan.tfplan
terraform apply plan.tfplan
```

Never commit `.tfvars` files with secrets. Prefer:

- Push `db_password` to AWS Secrets Manager and pull with `data.aws_secretsmanager_secret_version`
- Or use SSM Parameter Store SecureStrings
- Or supply `db_password` via `TF_VAR_db_password` in CI, sourced from OIDC-federated Vault / KMS

## Wire kubeconfig after apply

```bash
aws eks update-kubeconfig \
  --region $(terraform output -raw region) \
  --name   $(terraform output -raw cluster_name) \
  --alias  cymed-prod
kubectl config use-context cymed-prod
kubectl get nodes
```

## Local tooling summary

| Tool               | Purpose                                        |
|--------------------|------------------------------------------------|
| `terraform` >= 1.6 | Provision the AWS baseline in this directory   |
| `aws` CLI v2       | Auth, state-bucket bootstrap, kubeconfig       |
| `kubectl` >= 1.28  | Post-apply verification, apply Kustomize base  |
| `helm` >= 3.14     | Install cluster add-ons (ingress-nginx etc.)   |
| `kubeseal` >= 0.25 | Seal the Kubernetes Secret before committing   |
| `cosign` >= 2.2    | Verify container image signatures              |
| `checkov`          | Static analysis of terraform + kubernetes YAML |
