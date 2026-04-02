output "app_security_group_id" {
  description = "Security group ID for ECS tasks / app compute"
  value       = aws_security_group.app_tasks.id
}

output "app_runtime_secret_arn" {
  description = "Secrets Manager ARN for app runtime settings"
  value       = aws_secretsmanager_secret.app_runtime.arn
}

output "task_execution_role_arn" {
  description = "IAM role ARN for ECS task execution"
  value       = aws_iam_role.task_execution.arn
}

output "task_execution_role_name" {
  description = "IAM role name for ECS task execution"
  value       = aws_iam_role.task_execution.name
}

output "task_role_arn" {
  description = "IAM role ARN for the application task"
  value       = aws_iam_role.task.arn
}

output "task_role_name" {
  description = "IAM role name for the application task"
  value       = aws_iam_role.task.name
}
