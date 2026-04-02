terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

data "aws_region" "current" {}

data "aws_iam_policy_document" "ecs_tasks_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

locals {
  common_tags = {
    Project     = "ecommerce-erp"
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  secret_arns = distinct(concat([aws_secretsmanager_secret.app_runtime.arn], var.additional_secret_arns))
}

resource "aws_security_group" "app_tasks" {
  name        = "ecommerce-erp-app-${var.environment}"
  description = "Security group for ECS tasks and other application compute"
  vpc_id      = var.vpc_id

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "ecommerce-erp-app-${var.environment}"
  })
}

resource "random_password" "api_basic_auth" {
  length  = 24
  special = false
}

resource "aws_secretsmanager_secret" "app_runtime" {
  name                    = "ecommerce-erp/app/${var.environment}"
  description             = "Application runtime secrets for ecommerce-erp ${var.environment}"
  recovery_window_in_days = 0

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "app_runtime" {
  secret_id = aws_secretsmanager_secret.app_runtime.id
  secret_string = jsonencode({
    API_AUTH_ENABLED    = tostring(var.api_auth_enabled)
    API_BASIC_AUTH_USER = var.api_basic_auth_user
    API_BASIC_AUTH_PASS = random_password.api_basic_auth.result
    TAVILY_API_KEY      = var.tavily_api_key
    API_DB_BACKEND      = "postgres"
  })
}

resource "aws_iam_role" "task_execution" {
  name               = "ecommerce-erp-task-exec-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "task_execution_managed" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name               = "ecommerce-erp-task-app-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = local.common_tags
}

data "aws_iam_policy_document" "secret_access" {
  statement {
    sid = "ReadRuntimeSecrets"

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]

    resources = local.secret_arns
  }

  statement {
    sid = "DecryptSecretsManagerValues"

    actions   = ["kms:Decrypt"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${data.aws_region.current.name}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "task_execution_secrets" {
  name   = "ecommerce-erp-task-exec-secrets-${var.environment}"
  role   = aws_iam_role.task_execution.id
  policy = data.aws_iam_policy_document.secret_access.json
}

resource "aws_iam_role_policy" "task_secrets" {
  name   = "ecommerce-erp-task-app-secrets-${var.environment}"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.secret_access.json
}
