variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway in dev (set true only when explicitly testing private egress via NAT)"
  type        = bool
  default     = false
}

variable "single_nat_gateway" {
  description = "Use one shared NAT Gateway in dev when NAT is enabled"
  type        = bool
  default     = true
}
