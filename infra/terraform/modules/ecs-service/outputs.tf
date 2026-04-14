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

output "https_url" {
  description = "HTTPS URL for the public application when HTTPS is enabled"
  value       = var.enable_https ? "https://${coalesce(var.domain_name, aws_lb.this.dns_name)}" : null
}

output "custom_domain_url" {
  description = "Custom domain URL when Route 53 or an external certificate-backed domain is configured"
  value       = var.domain_name != null ? format("%s://%s", var.enable_https ? "https" : "http", var.domain_name) : null
}

output "certificate_arn" {
  description = "ACM certificate ARN attached to the ALB when HTTPS is enabled"
  value       = var.enable_https ? coalesce(var.certificate_arn, try(aws_acm_certificate_validation.this[0].certificate_arn, null)) : null
}
