variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway in dev only when explicitly testing private egress via NAT"
  type        = bool
  default     = false
}

variable "single_nat_gateway" {
  description = "Use one shared NAT Gateway in dev when NAT is enabled"
  type        = bool
  default     = true
}

variable "enable_vpc_endpoints" {
  description = "Enable private-subnet VPC endpoints for AWS service access without NAT"
  type        = bool
  default     = false
}

variable "interface_endpoint_services" {
  description = "Interface endpoint services to create when enable_vpc_endpoints=true"
  type        = list(string)
  default     = ["ecr.api", "ecr.dkr", "logs", "secretsmanager"]
}

variable "db_name" {
  description = "Initial application database name"
  type        = string
  default     = "ecommerce_erp"
}

variable "db_master_username" {
  description = "Master username for the Postgres instance"
  type        = string
  default     = "erp_admin"
}

variable "db_instance_class" {
  description = "RDS instance class for the dev database"
  type        = string
  default     = "db.t3.micro"
}

variable "db_engine_version" {
  description = "Optional Postgres engine version override. Leave null to let AWS choose a current default."
  type        = string
  default     = null
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in GiB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Autoscaling storage ceiling in GiB"
  type        = number
  default     = 100
}

variable "db_publicly_accessible" {
  description = "Whether the dev RDS instance should be publicly accessible"
  type        = bool
  default     = false
}

variable "db_backup_retention_period" {
  description = "How many days of automated backups to keep for dev"
  type        = number
  default     = 1
}

variable "db_deletion_protection" {
  description = "Enable deletion protection for the dev RDS instance"
  type        = bool
  default     = false
}

variable "db_skip_final_snapshot" {
  description = "Skip the final snapshot when destroying the dev RDS instance"
  type        = bool
  default     = true
}

variable "api_auth_enabled" {
  description = "Whether API basic auth should be enabled in cloud environments"
  type        = bool
  default     = true
}

variable "api_basic_auth_user" {
  description = "Username for API basic auth"
  type        = string
  default     = "admin"
}

variable "tavily_api_key" {
  description = "Optional Tavily API key to store in Secrets Manager (set via ignored tfvars or -var)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "tavily_mock" {
  description = "Keep Tavily in mock mode for the initial cloud deployment and smoke tests"
  type        = bool
  default     = true
}

variable "image_tag" {
  description = "Container image tag to deploy from ECR"
  type        = string
  default     = "latest"
}

variable "service_desired_count" {
  description = "Desired number of ECS tasks for the API service"
  type        = number
  default     = 1
}

variable "service_task_cpu" {
  description = "Fargate CPU units for the API task"
  type        = number
  default     = 256
}

variable "service_task_memory" {
  description = "Fargate memory in MiB for the API task"
  type        = number
  default     = 512
}

variable "service_subnet_type" {
  description = "Run ECS tasks in public or private subnets"
  type        = string
  default     = "public"
}

variable "service_assign_public_ip" {
  description = "Assign a public IP to ECS tasks (recommended for cheapest public-subnet dev mode)"
  type        = bool
  default     = true
}

variable "service_health_check_path" {
  description = "ALB health check path for the API"
  type        = string
  default     = "/healthz"
}

variable "wait_for_service_steady_state" {
  description = "Wait for ECS service steady state during apply"
  type        = bool
  default     = false
}

variable "enable_service_autoscaling" {
  description = "Enable target-tracking autoscaling for the ECS service"
  type        = bool
  default     = false
}

variable "service_min_capacity" {
  description = "Minimum desired task count when autoscaling is enabled"
  type        = number
  default     = 1
}

variable "service_max_capacity" {
  description = "Maximum desired task count when autoscaling is enabled"
  type        = number
  default     = 2
}

variable "service_autoscaling_cpu_target" {
  description = "Target average CPU utilization for ECS autoscaling"
  type        = number
  default     = 70
}

variable "enable_ui" {
  description = "Deploy the Streamlit UI on the public ALB"
  type        = bool
  default     = true
}

variable "ui_desired_count" {
  description = "Desired task count for the Streamlit UI service"
  type        = number
  default     = 1
}

variable "ui_task_cpu" {
  description = "Fargate CPU units for the Streamlit UI"
  type        = number
  default     = 256
}

variable "ui_task_memory" {
  description = "Fargate memory in MiB for the Streamlit UI"
  type        = number
  default     = 512
}

variable "ui_container_port" {
  description = "Container port for the Streamlit UI"
  type        = number
  default     = 8501
}

variable "ui_health_check_path" {
  description = "Health check path for the Streamlit UI target group"
  type        = string
  default     = "/_stcore/health"
}

variable "enable_https" {
  description = "Enable HTTPS on the ALB for the dev environment"
  type        = bool
  default     = false
}

variable "certificate_arn" {
  description = "Optional existing ACM certificate ARN for HTTPS"
  type        = string
  default     = null
}

variable "domain_name" {
  description = "Optional custom domain for the dev environment"
  type        = string
  default     = null
}

variable "route53_zone_id" {
  description = "Optional Route 53 hosted zone ID for ACM validation and alias records"
  type        = string
  default     = null
}

variable "subject_alternative_names" {
  description = "Optional SANs for a managed ACM certificate"
  type        = list(string)
  default     = []
}

variable "create_route53_record" {
  description = "Create the Route 53 alias record for the dev custom domain"
  type        = bool
  default     = false
}
