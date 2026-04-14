output "alb_dns_name" {
  description = "DNS name of the public Application Load Balancer"
  value       = aws_lb.this.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.this.arn
}

output "alb_security_group_id" {
  description = "Security group ID attached to the ALB"
  value       = aws_security_group.alb.id
}

output "target_group_arn" {
  description = "Target group ARN for the API service"
  value       = aws_lb_target_group.api.arn
}

output "ecs_service_name" {
  description = "ECS service name for the API"
  value       = aws_ecs_service.api.name
}

output "task_definition_arn" {
  description = "Task definition ARN for the deployed API service"
  value       = aws_ecs_task_definition.api.arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch Logs group receiving container logs"
  value       = aws_cloudwatch_log_group.app.name
}

output "service_url" {
  description = "Base HTTP URL for the public application load balancer"
  value       = "http://${aws_lb.this.dns_name}"
}

output "ui_service_name" {
  description = "ECS service name for the Streamlit UI"
  value       = var.enable_ui ? aws_ecs_service.ui[0].name : null
}

output "ui_url" {
  description = "HTTP URL for the public Streamlit UI"
  value       = var.enable_ui ? "http://${aws_lb.this.dns_name}" : null
}
