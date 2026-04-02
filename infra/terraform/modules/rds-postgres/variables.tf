variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the database will live"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to connect to Postgres"
  type        = list(string)
}

variable "db_name" {
  description = "Initial application database name"
  type        = string
  default     = "ecommerce_erp"
}

variable "master_username" {
  description = "Master username for the Postgres instance"
  type        = string
  default     = "erp_admin"
}

variable "instance_class" {
  description = "RDS instance class for the dev database"
  type        = string
  default     = "db.t3.micro"
}

variable "engine_version" {
  description = "Optional Postgres engine version. Leave null to let AWS choose a current default."
  type        = string
  default     = null
}

variable "allocated_storage" {
  description = "Initial allocated storage in GiB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Autoscaling ceiling for storage in GiB"
  type        = number
  default     = 100
}

variable "publicly_accessible" {
  description = "Whether the RDS instance should receive a public IP"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "How many days to keep automated backups"
  type        = number
  default     = 1
}

variable "deletion_protection" {
  description = "Enable deletion protection for the database"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip the final snapshot on destroy (recommended for dev/test)"
  type        = bool
  default     = true
}
