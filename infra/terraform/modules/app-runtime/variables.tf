variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where ECS tasks or other app compute will run"
  type        = string
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
  description = "Optional Tavily API key to store in Secrets Manager"
  type        = string
  default     = ""
  sensitive   = true
}

variable "additional_secret_arns" {
  description = "Additional Secrets Manager ARNs the ECS roles should be allowed to read"
  type        = list(string)
  default     = []
}
