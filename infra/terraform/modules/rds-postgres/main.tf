terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

locals {
  common_tags = {
    Project     = "ecommerce-erp"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "random_password" "master" {
  length  = 24
  special = false
}

resource "aws_db_subnet_group" "this" {
  name       = "ecommerce-erp-${var.environment}-db-subnets"
  subnet_ids = var.private_subnet_ids

  tags = merge(local.common_tags, {
    Name = "ecommerce-erp-${var.environment}-db-subnets"
  })
}

resource "aws_security_group" "database" {
  name        = "ecommerce-erp-rds-${var.environment}"
  description = "Postgres access for approved internal clients"
  vpc_id      = var.vpc_id

  ingress {
    description = "Postgres from approved internal CIDR blocks"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "ecommerce-erp-rds-${var.environment}"
  })
}

resource "aws_db_instance" "this" {
  identifier                 = "ecommerce-erp-${var.environment}-postgres"
  engine                     = "postgres"
  engine_version             = var.engine_version
  instance_class             = var.instance_class
  allocated_storage          = var.allocated_storage
  max_allocated_storage      = var.max_allocated_storage
  storage_type               = "gp3"
  storage_encrypted          = true
  db_name                    = var.db_name
  username                   = var.master_username
  password                   = random_password.master.result
  db_subnet_group_name       = aws_db_subnet_group.this.name
  vpc_security_group_ids     = [aws_security_group.database.id]
  publicly_accessible        = var.publicly_accessible
  multi_az                   = false
  backup_retention_period    = var.backup_retention_period
  deletion_protection        = var.deletion_protection
  skip_final_snapshot        = var.skip_final_snapshot
  copy_tags_to_snapshot      = true
  apply_immediately          = true
  auto_minor_version_upgrade = true

  tags = merge(local.common_tags, {
    Name = "ecommerce-erp-${var.environment}-postgres"
  })
}

resource "aws_secretsmanager_secret" "db_connection" {
  name                    = "ecommerce-erp/db/${var.environment}"
  description             = "RDS PostgreSQL connection details for ecommerce-erp ${var.environment}"
  recovery_window_in_days = 0

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_connection" {
  secret_id = aws_secretsmanager_secret.db_connection.id
  secret_string = jsonencode({
    engine   = "postgres"
    host     = aws_db_instance.this.address
    port     = aws_db_instance.this.port
    dbname   = var.db_name
    username = var.master_username
    password = random_password.master.result
    dsn      = "postgresql://${var.master_username}:${random_password.master.result}@${aws_db_instance.this.address}:${aws_db_instance.this.port}/${var.db_name}"
  })
}
