data "aws_region" "current" {}

locals {
  common_tags = {
    Project     = "ecommerce-erp"
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  service_subnet_ids = var.service_subnet_type == "private" ? var.private_subnet_ids : var.public_subnet_ids
  container_name     = "ecommerce-erp-api"
  container_env = [
    {
      name  = "API_HOST"
      value = "0.0.0.0"
    },
    {
      name  = "API_PORT"
      value = tostring(var.container_port)
    },
    {
      name  = "API_DB_BACKEND"
      value = "postgres"
    },
    {
      name  = "TAVILY_MOCK"
      value = var.tavily_mock ? "true" : "false"
    }
  ]

  container_secrets = [
    {
      name      = "API_AUTH_ENABLED"
      valueFrom = "${var.app_runtime_secret_arn}:API_AUTH_ENABLED::"
    },
    {
      name      = "API_BASIC_AUTH_USER"
      valueFrom = "${var.app_runtime_secret_arn}:API_BASIC_AUTH_USER::"
    },
    {
      name      = "API_BASIC_AUTH_PASS"
      valueFrom = "${var.app_runtime_secret_arn}:API_BASIC_AUTH_PASS::"
    },
    {
      name      = "TAVILY_API_KEY"
      valueFrom = "${var.app_runtime_secret_arn}:TAVILY_API_KEY::"
    },
    {
      name      = "API_POSTGRES_DSN"
      valueFrom = "${var.db_secret_arn}:dsn::"
    }
  ]
}

resource "aws_security_group" "alb" {
  name        = "ecommerce-erp-alb-${var.environment}"
  description = "Public ALB for ecommerce-erp ${var.environment}"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from the internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "ecommerce-erp-alb-${var.environment}"
  })
}

resource "aws_security_group_rule" "app_ingress_from_alb" {
  type                     = "ingress"
  from_port                = var.container_port
  to_port                  = var.container_port
  protocol                 = "tcp"
  security_group_id        = var.app_security_group_id
  source_security_group_id = aws_security_group.alb.id
  description              = "Allow ALB traffic to the application"
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/ecs/ecommerce-erp-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_lb" "this" {
  name               = "ecommerce-erp-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.alb_deletion_protection

  tags = merge(local.common_tags, {
    Name = "ecommerce-erp-${var.environment}"
  })
}

resource "aws_lb_target_group" "api" {
  name        = "ecom-erp-${var.environment}-api"
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = var.health_check_path
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = merge(local.common_tags, {
    Name = "ecom-erp-${var.environment}-api"
  })
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "ecommerce-erp-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = local.container_name
      image     = "${var.ecr_repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = local.container_env
      secrets     = local.container_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_service" "api" {
  name                               = "ecommerce-erp-api-${var.environment}"
  cluster                            = var.ecs_cluster_arn
  task_definition                    = aws_ecs_task_definition.api.arn
  desired_count                      = var.desired_count
  launch_type                        = "FARGATE"
  health_check_grace_period_seconds  = 60
  wait_for_steady_state              = var.wait_for_steady_state
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = local.service_subnet_ids
    security_groups  = [var.app_security_group_id]
    assign_public_ip = var.assign_public_ip
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = local.container_name
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.http]

  tags = local.common_tags
}

resource "aws_appautoscaling_target" "ecs" {
  count = var.enable_autoscaling ? 1 : 0

  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${var.ecs_cluster_name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  count = var.enable_autoscaling ? 1 : 0

  name               = "ecommerce-erp-cpu-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    target_value       = var.autoscaling_cpu_target
    scale_in_cooldown  = 60
    scale_out_cooldown = 60
  }
}
