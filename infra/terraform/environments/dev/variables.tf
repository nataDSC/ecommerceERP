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
