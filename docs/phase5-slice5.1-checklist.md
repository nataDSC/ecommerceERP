# Phase 5 · Slice 5.1 — Platform & Networking Foundation

> **Goal:** Lay the AWS foundation that every later slice depends on:
> an ECR image registry, a production-ready VPC, and a Terraform workspace
> that can reproduce any environment deterministically.

---

## Naming conventions

| Resource               | Pattern                              | Example                       |
| ---------------------- | ------------------------------------ | ----------------------------- |
| Project prefix         | `ecommerce-erp`                      | —                             |
| Environment suffix     | `-dev`, `-staging`, `-prod`          | —                             |
| ECR repo               | `ecommerce-erp`                      | (one repo, multiple tags)     |
| Image tag              | `<git-sha>` + `latest`               | `a1b2c3d`, `latest`           |
| VPC                    | `ecommerce-erp-vpc-<env>`            | `ecommerce-erp-vpc-dev`       |
| ECS cluster            | `ecommerce-erp-<env>`                | `ecommerce-erp-dev`           |
| IAM role (task exec)   | `ecommerce-erp-task-exec-<env>`      | `ecommerce-erp-task-exec-dev` |
| Terraform state bucket | `ecommerce-erp-tfstate-<account-id>` | —                             |
| Terraform workspace    | `dev` / `staging` / `prod`           | `dev`                         |

---

## Pre-flight checklist

- [ ] AWS CLI v2 installed and `aws configure` completed (or SSO profile configured)
- [ ] Terraform ≥ 1.6 installed (`terraform -version`)
- [ ] Docker daemon running (ECR push test)
- [ ] Target AWS account ID noted (you'll need it for the state bucket name)
- [ ] Target region chosen — set `AWS_DEFAULT_REGION` (e.g. `us-east-1`)

---

## Step 1 — Bootstrap Terraform remote state

Create an S3 bucket + DynamoDB table for Terraform state locking.
Do this once per account; it is shared across all environments.

```bash
# Set these once in your shell
export AWS_DEFAULT_REGION=us-east-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export TF_STATE_BUCKET="ecommerce-erp-tfstate-${ACCOUNT_ID}"

# Create state bucket (versioning on, public access blocked)
aws s3api create-bucket \
  --bucket "${TF_STATE_BUCKET}" \
  --region "${AWS_DEFAULT_REGION}"
  # This flag should not be used for the default region us-east-1, it is assumed
  # \
  # --create-bucket-configuration LocationConstraint="${AWS_DEFAULT_REGION}"

aws s3api put-bucket-versioning \
  --bucket "${TF_STATE_BUCKET}" \
  --versioning-configuration Status=Enabled

aws s3api put-public-access-block \
  --bucket "${TF_STATE_BUCKET}" \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name ecommerce-erp-tflock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

> **Security note:** Never commit state bucket names or account IDs to git.
> Export them from your shell or a local `.envrc` (add `.envrc` to `.gitignore`).

---

## Step 2 — Terraform directory layout

Create the following structure under `infra/`:

```
infra/
  terraform/
    modules/
      vpc/
        main.tf
        variables.tf
        outputs.tf
      ecr/
        main.tf
        variables.tf
        outputs.tf
      ecs-cluster/
        main.tf
        variables.tf
        outputs.tf
    environments/
      dev/
        main.tf          # calls modules, sets env-specific vars
        variables.tf
        terraform.tfvars # NOT committed — add to .gitignore
        backend.tf       # points to S3 state bucket
      staging/
        (same layout)
      prod/
        (same layout)
```

---

## Step 3 — ECR repository

**Module:** `infra/terraform/modules/ecr/main.tf`

```hcl
resource "aws_ecr_repository" "api" {
  name                 = "ecommerce-erp"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true   # free vulnerability scan on every push
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Project     = "ecommerce-erp"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Lifecycle: keep last 10 tagged images, purge untagged after 1 day
resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Purge untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep last 10 tagged builds"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}

output "repository_url" {
  value = aws_ecr_repository.api.repository_url
}
```

---

## Step 4 — VPC

**Module:** `infra/terraform/modules/vpc/main.tf`

Key design decisions:

- 2 Availability Zones minimum (3 recommended for prod)
- Public subnets → ALB and the cheapest ECS dev/test path
- Private subnets → ECS tasks, RDS (Slice 5.2)
- NAT is optional and now defaults to **off** in `dev`
- VPC endpoints are optional for private-subnet / no-NAT mode; use them for isolation, not because they are always cheaper

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "ecommerce-erp-vpc-${var.environment}"
  cidr = var.vpc_cidr

  azs             = formatlist("${var.aws_region}%s", ["a", "b"])
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = var.enable_nat_gateway
  single_nat_gateway   = var.single_nat_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_vpc_endpoint" "s3" {
  count = var.enable_vpc_endpoints ? 1 : 0
  # Interface endpoints for `ecr.api`, `ecr.dkr`, and `logs` are also optional.
}
```

### Network mode quick reference

| Mode                | Terraform flags                    | Best for                        | Cost note                                                       |
| ------------------- | ---------------------------------- | ------------------------------- | --------------------------------------------------------------- |
| Public-subnet dev   | none (defaults)                    | cheapest AWS dev/test path      | lowest cost                                                     |
| NAT practice        | `-var="enable_nat_gateway=true"`   | learning private egress via NAT | NAT is usually the largest fixed cost                           |
| Private + endpoints | `-var="enable_vpc_endpoints=true"` | no-NAT private-subnet pattern   | more isolated, but interface endpoints also have hourly charges |

> Uses the [terraform-aws-modules/vpc](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws) community module — battle-tested, no custom code to maintain.

---

## Step 5 — ECS cluster

**Module:** `infra/terraform/modules/ecs-cluster/main.tf`

```hcl
resource "aws_ecs_cluster" "main" {
  name = "ecommerce-erp-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"   # CloudWatch Container Insights (free tier covers basics)
  }

  tags = {
    Project     = "ecommerce-erp"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

output "cluster_arn"  { value = aws_ecs_cluster.main.arn }
output "cluster_name" { value = aws_ecs_cluster.main.name }
```

---

## Step 6 — Dev environment root module

**File:** `infra/terraform/environments/dev/backend.tf`

```hcl
terraform {
  backend "s3" {
    # Values injected at `terraform init` time — do NOT hardcode account IDs here
    bucket         = ""          # override: -backend-config="bucket=ecommerce-erp-tfstate-<account>"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ecommerce-erp-tflock"
    encrypt        = true
  }
}
```

**File:** `infra/terraform/environments/dev/main.tf`

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.6"
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "ecommerce-erp"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

module "vpc" {
  source                   = "../../modules/vpc"
  environment              = "dev"
  aws_region               = var.aws_region
  enable_nat_gateway       = var.enable_nat_gateway
  single_nat_gateway       = var.single_nat_gateway
  enable_vpc_endpoints     = var.enable_vpc_endpoints
  interface_endpoint_services = var.interface_endpoint_services
}

module "ecr" {
  source      = "../../modules/ecr"
  environment = "dev"
}

module "ecs_cluster" {
  source      = "../../modules/ecs-cluster"
  environment = "dev"
}
```

---

## Step 7 — First apply

```bash
cd infra/terraform/environments/dev

# Init (inject state bucket name at init time — not hardcoded in backend.tf)
terraform init \
  -backend-config="bucket=${TF_STATE_BUCKET}"

# Cheapest dev default: NAT off, endpoints off
terraform plan
terraform apply

# NAT practice mode (single NAT Gateway)
terraform plan -var="enable_nat_gateway=true" -var="single_nat_gateway=true"
terraform apply -var="enable_nat_gateway=true" -var="single_nat_gateway=true"

# Private-subnet / no-NAT mode using VPC endpoints
terraform plan -var="enable_vpc_endpoints=true"
terraform apply -var="enable_vpc_endpoints=true"
```

Expected output (approximate):

```
Plan size varies by network mode:
- ~18 resources: NAT off, endpoints off
- ~23 resources: single NAT enabled
- ~22-26 resources: endpoints enabled (depends on services selected)

Outputs:
ecr_repository_url    = "123456789.dkr.ecr.us-east-1.amazonaws.com/ecommerce-erp"
ecs_cluster_name      = "ecommerce-erp-dev"
vpc_id                = "vpc-0abc..."
private_subnet_ids    = ["subnet-0...", "subnet-0..."]
public_subnet_ids     = ["subnet-0...", "subnet-0..."]
vpc_endpoint_ids      = []  # or populated when enable_vpc_endpoints=true
```

> Use the same `-var` flags with `terraform destroy` that you used with `terraform apply`.

---

## Step 8 — Verify ECR push

Confirm the local Docker image can push to the new registry:

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region "${AWS_DEFAULT_REGION}" \
  | docker login --username AWS --password-stdin \
    "${ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"

# Tag and push the image built locally in Phase 4
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ecommerce-erp"
GIT_SHA=$(git rev-parse --short HEAD)

docker tag ecommerce-erp-api:local "${ECR_REPO}:${GIT_SHA}"
docker tag ecommerce-erp-api:local "${ECR_REPO}:latest"

docker push "${ECR_REPO}:${GIT_SHA}"
docker push "${ECR_REPO}:latest"
```

Run ECR scan results check (optional but recommended):

```bash
aws ecr describe-image-scan-findings \
  --repository-name ecommerce-erp \
  --image-id imageTag="${GIT_SHA}" \
  --query 'imageScanFindings.findingSeverityCounts'
```

---

## .gitignore additions

Add these lines to `.gitignore` before committing anything in `infra/`:

```gitignore
# Terraform
infra/terraform/**/.terraform/
infra/terraform/**/*.tfstate
infra/terraform/**/*.tfstate.backup
infra/terraform/**/*.tfvars
infra/terraform/**/.terraform.lock.hcl
.envrc
```

---

## Slice 5.1 completion criteria

- [ ] `terraform apply` succeeds with 0 errors in dev environment
- [ ] ECR repository visible in AWS console at `ecommerce-erp`
- [ ] `docker push` to ECR succeeds and image appears in console
- [ ] ECS cluster `ecommerce-erp-dev` visible with Container Insights enabled
- [ ] VPC with 2 public + 2 private subnets in 2 AZs
- [ ] State file stored in S3 (verify: `aws s3 ls s3://${TF_STATE_BUCKET}/dev/`)
- [ ] No secrets or account IDs committed to git

---

## Hand-off to Slice 5.2

Once this checklist is fully checked off, Slice 5.2 needs:

- `vpc_id` output
- `private_subnet_ids` output
- ECR `repository_url` output

These will be referenced by the RDS, Secrets Manager, and ECS task definition resources.
