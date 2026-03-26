terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
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
  source      = "../../modules/vpc"
  environment = "dev"
  aws_region  = var.aws_region
}

module "ecr" {
  source      = "../../modules/ecr"
  environment = "dev"
}

module "ecs_cluster" {
  source      = "../../modules/ecs-cluster"
  environment = "dev"
}
