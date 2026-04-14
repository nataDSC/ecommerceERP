output "dashboard_name" {
  description = "CloudWatch dashboard name for the dev environment"
  value       = var.create_dashboard ? aws_cloudwatch_dashboard.main[0].dashboard_name : null
}

output "alarm_names" {
  description = "Core CloudWatch alarm names created for the environment"
  value = var.create_alarms ? [
    aws_cloudwatch_metric_alarm.alb_unhealthy_hosts[0].alarm_name,
    aws_cloudwatch_metric_alarm.alb_target_5xx[0].alarm_name,
    aws_cloudwatch_metric_alarm.ecs_api_running_tasks_low[0].alarm_name
  ] : []
}

output "sns_topic_arn" {
  description = "SNS topic ARN for observability notifications when enabled"
  value       = var.create_sns_topic ? aws_sns_topic.alerts[0].arn : null
}
