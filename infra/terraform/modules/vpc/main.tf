module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "ecommerce-erp-vpc-${var.environment}"
  cidr = var.vpc_cidr

  azs             = formatlist("${var.aws_region}%s", ["a", "b"])
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = var.enable_nat_gateway
  single_nat_gateway   = var.single_nat_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Project     = "ecommerce-erp"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
