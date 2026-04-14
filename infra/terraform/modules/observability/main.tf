locals {
  common_tags = {
    Project     = "ecommerce-erp"
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  alb_arn_suffix          = join("/", slice(split("/", var.alb_arn), 1, length(split("/", var.alb_arn))))
  target_group_arn_suffix = join("/", slice(split("/", var.target_group_arn), 1, length(split("/", var.target_group_arn))))
  effective_alarm_actions = concat(var.alarm_action_arns, var.create_sns_topic ? [aws_sns_topic.alerts[0].arn] : [])

  dashboard_widgets = concat(
    [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "ALB Requests and 5XX"
          region  = var.aws_region
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", local.alb_arn_suffix, { stat = "Sum", label = "Requests" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "TargetGroup", local.target_group_arn_suffix, "LoadBalancer", local.alb_arn_suffix, { stat = "Sum", label = "Target 5XX" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "ALB Target Health"
          region  = var.aws_region
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/ApplicationELB", "HealthyHostCount", "TargetGroup", local.target_group_arn_suffix, "LoadBalancer", local.alb_arn_suffix, { stat = "Average", label = "Healthy hosts" }],
            ["AWS/ApplicationELB", "UnHealthyHostCount", "TargetGroup", local.target_group_arn_suffix, "LoadBalancer", local.alb_arn_suffix, { stat = "Average", label = "Unhealthy hosts" }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "ECS Services"
          region  = var.aws_region
          view    = "timeSeries"
          stacked = false
          metrics = concat(
            [
              ["AWS/ECS", "CPUUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", var.api_service_name, { stat = "Average", label = "API CPU %" }],
              ["AWS/ECS", "MemoryUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", var.api_service_name, { stat = "Average", label = "API Memory %" }],
              ["AWS/ECS", "RunningTaskCount", "ClusterName", var.ecs_cluster_name, "ServiceName", var.api_service_name, { stat = "Average", label = "API running tasks" }]
            ],
            var.ui_service_name != null ? [
              ["AWS/ECS", "CPUUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", var.ui_service_name, { stat = "Average", label = "UI CPU %" }],
              ["AWS/ECS", "MemoryUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", var.ui_service_name, { stat = "Average", label = "UI Memory %" }],
              ["AWS/ECS", "RunningTaskCount", "ClusterName", var.ecs_cluster_name, "ServiceName", var.ui_service_name, { stat = "Average", label = "UI running tasks" }]
            ] : []
          )
        }
      }
    ],
    var.db_identifier != null ? [
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "RDS Health"
          region  = var.aws_region
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.db_identifier, { stat = "Average", label = "DB CPU %" }],
            ["AWS/RDS", "FreeStorageSpace", "DBInstanceIdentifier", var.db_identifier, { stat = "Average", label = "Free storage bytes" }]
          ]
        }
      }
    ] : []
  )
}

resource "aws_sns_topic" "alerts" {
  count = var.create_sns_topic ? 1 : 0

  name = "ecommerce-erp-${var.environment}-alerts"

  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "email" {
  count = var.create_sns_topic && var.alert_email_address != null ? 1 : 0

  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email_address
}

resource "aws_cloudwatch_dashboard" "main" {
  count = var.create_dashboard ? 1 : 0

  dashboard_name = "ecommerce-erp-${var.environment}-overview"
  dashboard_body = jsonencode({
    widgets = local.dashboard_widgets
  })
}

resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  count = var.create_alarms ? 1 : 0

  alarm_name          = "ecommerce-erp-${var.environment}-alb-unhealthy-hosts"
  alarm_description   = "ALB target group has unhealthy hosts for the ecommerce-erp ${var.environment} stack"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Average"
  period              = 60
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.effective_alarm_actions
  ok_actions          = local.effective_alarm_actions

  dimensions = {
    LoadBalancer = local.alb_arn_suffix
    TargetGroup  = local.target_group_arn_suffix
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "alb_target_5xx" {
  count = var.create_alarms ? 1 : 0

  alarm_name          = "ecommerce-erp-${var.environment}-alb-target-5xx"
  alarm_description   = "ALB target 5XX errors exceeded the dev threshold for ecommerce-erp ${var.environment}"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 3
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.effective_alarm_actions
  ok_actions          = local.effective_alarm_actions

  dimensions = {
    LoadBalancer = local.alb_arn_suffix
    TargetGroup  = local.target_group_arn_suffix
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "ecs_api_running_tasks_low" {
  count = var.create_alarms ? 1 : 0

  alarm_name          = "ecommerce-erp-${var.environment}-ecs-api-running-low"
  alarm_description   = "API ECS running task count dropped below the expected level for ecommerce-erp ${var.environment}"
  namespace           = "AWS/ECS"
  metric_name         = "RunningTaskCount"
  statistic           = "Average"
  period              = 60
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = var.api_desired_count
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.effective_alarm_actions
  ok_actions          = local.effective_alarm_actions

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.api_service_name
  }

  tags = local.common_tags
}
