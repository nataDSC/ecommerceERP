output "ecr_repository_url" {
  description = "ECR repository URL for docker push"
  value       = module.ecr.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs_cluster.cluster_name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = module.ecs_cluster.cluster_arn
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs (for ECS tasks and RDS)"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs (for ALB)"
  value       = module.vpc.public_subnet_ids
}

output "vpc_endpoint_ids" {
  description = "VPC endpoint IDs created for private-subnet / no-NAT mode"
  value       = module.vpc.vpc_endpoint_ids
}

output "vpc_cidr_block" {
  description = "CIDR block of the provisioned VPC"
  value       = module.vpc.vpc_cidr_block
}

output "app_security_group_id" {
  description = "Security group ID for future ECS tasks / app compute"
  value       = module.app_runtime.app_security_group_id
}

output "app_runtime_secret_arn" {
  description = "Secrets Manager ARN for app runtime values"
  value       = module.app_runtime.app_runtime_secret_arn
}

output "task_execution_role_arn" {
  description = "IAM role ARN for ECS task execution"
  value       = module.app_runtime.task_execution_role_arn
}

output "task_role_arn" {
  description = "IAM role ARN for the application task"
  value       = module.app_runtime.task_role_arn
}

output "db_identifier" {
  description = "RDS instance identifier"
  value       = module.rds_postgres.db_identifier
}

output "db_endpoint" {
  description = "RDS endpoint hostname"
  value       = module.rds_postgres.db_endpoint
}

output "db_port" {
  description = "RDS endpoint port"
  value       = module.rds_postgres.db_port
}

output "db_name" {
  description = "Application database name"
  value       = module.rds_postgres.db_name
}

output "db_secret_arn" {
  description = "Secrets Manager ARN containing DB connection details"
  value       = module.rds_postgres.db_secret_arn
}
