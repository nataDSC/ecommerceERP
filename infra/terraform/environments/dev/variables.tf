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
  default     = ["ecr.api", "ecr.dkr", "logs"]
}
