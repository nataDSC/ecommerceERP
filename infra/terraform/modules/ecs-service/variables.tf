variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for ALB and ECS service networking"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the internet-facing ALB"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks when service_subnet_type=private"
  type        = list(string)
}

variable "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "app_security_group_id" {
  description = "Security group ID to attach to ECS tasks"
  type        = string
}

variable "task_execution_role_arn" {
  description = "IAM role ARN for ECS task execution"
  type        = string
}

variable "task_role_arn" {
  description = "IAM role ARN for the application task"
  type        = string
}

variable "app_runtime_secret_arn" {
  description = "Secrets Manager ARN with application runtime values"
  type        = string
}

variable "db_secret_arn" {
  description = "Secrets Manager ARN containing the database DSN"
  type        = string
}

variable "ecr_repository_url" {
  description = "ECR repository URL without the image tag"
  type        = string
}

variable "image_tag" {
  description = "Container image tag to deploy from ECR"
  type        = string
  default     = "latest"
}

variable "container_port" {
  description = "Application container port exposed by the API"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 1
}

variable "task_cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Fargate task memory in MiB"
  type        = number
  default     = 512
}

variable "service_subnet_type" {
  description = "Whether ECS tasks should run in public or private subnets"
  type        = string
  default     = "public"

  validation {
    condition     = contains(["public", "private"], var.service_subnet_type)
    error_message = "service_subnet_type must be either 'public' or 'private'."
  }
}

variable "assign_public_ip" {
  description = "Assign a public IP to ECS tasks (typically true for public-subnet dev mode)"
  type        = bool
  default     = true
}

variable "health_check_path" {
  description = "ALB health check path"
  type        = string
  default     = "/healthz"
}

variable "alb_deletion_protection" {
  description = "Enable deletion protection on the ALB"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "wait_for_steady_state" {
  description = "Wait for ECS service steady state during apply"
  type        = bool
  default     = false
}

variable "enable_autoscaling" {
  description = "Enable target-tracking autoscaling for the ECS service"
  type        = bool
  default     = false
}

variable "min_capacity" {
  description = "Minimum desired count when autoscaling is enabled"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum desired count when autoscaling is enabled"
  type        = number
  default     = 2
}

variable "autoscaling_cpu_target" {
  description = "Target average CPU utilization percentage for ECS autoscaling"
  type        = number
  default     = 70
}

variable "tavily_mock" {
  description = "Set true to keep Tavily in mock mode for cloud smoke tests"
  type        = bool
  default     = true
}

variable "enable_ui" {
  description = "Whether to deploy the Streamlit UI on the same ALB"
  type        = bool
  default     = false
}

variable "ui_container_port" {
  description = "Application container port exposed by the Streamlit UI"
  type        = number
  default     = 8501
}

variable "ui_health_check_path" {
  description = "ALB health check path for the Streamlit UI"
  type        = string
  default     = "/_stcore/health"
}

variable "ui_desired_count" {
  description = "Desired number of ECS tasks for the UI service"
  type        = number
  default     = 1
}

variable "ui_task_cpu" {
  description = "Fargate task CPU units for the UI task"
  type        = number
  default     = 256
}

variable "ui_task_memory" {
  description = "Fargate task memory in MiB for the UI task"
  type        = number
  default     = 512
}

variable "enable_https" {
  description = "Enable HTTPS on the public ALB"
  type        = bool
  default     = false
}

variable "certificate_arn" {
  description = "Existing ACM certificate ARN to attach to the HTTPS listener"
  type        = string
  default     = null
}

variable "domain_name" {
  description = "Optional custom domain name for the public application"
  type        = string
  default     = null
}

variable "route53_zone_id" {
  description = "Optional Route 53 hosted zone ID used for ACM DNS validation and alias record creation"
  type        = string
  default     = null
}

variable "subject_alternative_names" {
  description = "Optional SANs for a managed ACM certificate"
  type        = list(string)
  default     = []
}

variable "create_route53_record" {
  description = "Create a Route 53 alias record for the custom domain"
  type        = bool
  default     = false
}
