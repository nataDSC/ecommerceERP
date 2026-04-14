variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "alb_arn" {
  description = "ARN of the Application Load Balancer to protect"
  type        = string
}

variable "create_waf" {
  description = "Whether to create and attach the WAF web ACL"
  type        = bool
  default     = true
}

variable "rate_limit_per_5_minutes" {
  description = "Maximum requests per 5-minute window from a single IP before the WAF blocks it"
  type        = number
  default     = 1000
}
