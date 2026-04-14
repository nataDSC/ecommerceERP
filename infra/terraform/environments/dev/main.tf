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

module "ecs_service" {
  source                    = "../../modules/ecs-service"
  environment               = "dev"
  vpc_id                    = module.vpc.vpc_id
  public_subnet_ids         = module.vpc.public_subnet_ids
  private_subnet_ids        = module.vpc.private_subnet_ids
  ecs_cluster_arn           = module.ecs_cluster.cluster_arn
  ecs_cluster_name          = module.ecs_cluster.cluster_name
  app_security_group_id     = module.app_runtime.app_security_group_id
  task_execution_role_arn   = module.app_runtime.task_execution_role_arn
  task_role_arn             = module.app_runtime.task_role_arn
  app_runtime_secret_arn    = module.app_runtime.app_runtime_secret_arn
  db_secret_arn             = module.rds_postgres.db_secret_arn
  ecr_repository_url        = module.ecr.repository_url
  image_tag                 = var.image_tag
  desired_count             = var.service_desired_count
  task_cpu                  = var.service_task_cpu
  task_memory               = var.service_task_memory
  service_subnet_type       = var.service_subnet_type
  assign_public_ip          = var.service_assign_public_ip
  health_check_path         = var.service_health_check_path
  wait_for_steady_state     = var.wait_for_service_steady_state
  enable_autoscaling        = var.enable_service_autoscaling
  min_capacity              = var.service_min_capacity
  max_capacity              = var.service_max_capacity
  autoscaling_cpu_target    = var.service_autoscaling_cpu_target
  tavily_mock               = var.tavily_mock
  enable_ui                 = var.enable_ui
  ui_desired_count          = var.ui_desired_count
  ui_task_cpu               = var.ui_task_cpu
  ui_task_memory            = var.ui_task_memory
  ui_container_port         = var.ui_container_port
  ui_health_check_path      = var.ui_health_check_path
  enable_https              = var.enable_https
  certificate_arn           = var.certificate_arn
  domain_name               = var.domain_name
  route53_zone_id           = var.route53_zone_id
  subject_alternative_names = var.subject_alternative_names
  create_route53_record     = var.create_route53_record
}
