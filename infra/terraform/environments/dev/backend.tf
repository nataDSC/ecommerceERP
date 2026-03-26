terraform {
  # Backend values are injected at `terraform init` time with -backend-config flags.
  # Do NOT hardcode bucket names or account IDs here.
  backend "s3" {
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ecommerce-erp-tflock"
    encrypt        = true
  }
}
