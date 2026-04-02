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
  source                      = "../../modules/vpc"
  environment                 = "dev"
  aws_region                  = var.aws_region
  enable_nat_gateway          = var.enable_nat_gateway
  single_nat_gateway          = var.single_nat_gateway
  enable_vpc_endpoints        = var.enable_vpc_endpoints
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

module "rds_postgres" {
  source                  = "../../modules/rds-postgres"
  environment             = "dev"
  vpc_id                  = module.vpc.vpc_id
  private_subnet_ids      = module.vpc.private_subnet_ids
  allowed_cidr_blocks     = [module.vpc.vpc_cidr_block]
  db_name                 = var.db_name
  master_username         = var.db_master_username
  instance_class          = var.db_instance_class
  engine_version          = var.db_engine_version
  allocated_storage       = var.db_allocated_storage
  max_allocated_storage   = var.db_max_allocated_storage
  publicly_accessible     = var.db_publicly_accessible
  backup_retention_period = var.db_backup_retention_period
  deletion_protection     = var.db_deletion_protection
  skip_final_snapshot     = var.db_skip_final_snapshot
}

module "app_runtime" {
  source                 = "../../modules/app-runtime"
  environment            = "dev"
  vpc_id                 = module.vpc.vpc_id
  api_auth_enabled       = var.api_auth_enabled
  api_basic_auth_user    = var.api_basic_auth_user
  tavily_api_key         = var.tavily_api_key
  additional_secret_arns = [module.rds_postgres.db_secret_arn]
}
