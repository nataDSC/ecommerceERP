output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of private subnets (used by ECS tasks and RDS)"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "IDs of public subnets (used by ALB and NAT gateways)"
  value       = module.vpc.public_subnets
}
