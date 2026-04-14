variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region for dashboard widgets and alarms"
  type        = string
}

variable "ecs_cluster_name" {
  description = "ECS cluster name used by the application"
  type        = string
}

variable "api_service_name" {
  description = "Primary API ECS service name"
  type        = string
}

variable "api_desired_count" {
  description = "Expected desired count for the API ECS service"
  type        = number
  default     = 1
}

variable "ui_service_name" {
  description = "Optional Streamlit UI ECS service name"
  type        = string
  default     = null
}

variable "alb_arn" {
  description = "Application Load Balancer ARN"
  type        = string
}

variable "target_group_arn" {
  description = "Primary API target group ARN"
  type        = string
}

variable "db_identifier" {
  description = "Optional RDS instance identifier for dashboard metrics"
  type        = string
  default     = null
}

variable "create_dashboard" {
  description = "Create the CloudWatch dashboard"
  type        = bool
  default     = true
}

variable "create_alarms" {
  description = "Create the core CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alarm_action_arns" {
  description = "Optional existing alarm action ARNs, such as SNS topics"
  type        = list(string)
  default     = []
}

variable "create_sns_topic" {
  description = "Create an SNS topic for alert notifications"
  type        = bool
  default     = false
}

variable "alert_email_address" {
  description = "Optional email address to subscribe to the SNS alert topic"
  type        = string
  default     = null
}
