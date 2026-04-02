output "db_identifier" {
  description = "RDS instance identifier"
  value       = aws_db_instance.this.identifier
}

output "db_endpoint" {
  description = "RDS endpoint hostname"
  value       = aws_db_instance.this.address
}

output "db_port" {
  description = "RDS endpoint port"
  value       = aws_db_instance.this.port
}

output "db_name" {
  description = "Application database name"
  value       = var.db_name
}

output "db_secret_arn" {
  description = "Secrets Manager ARN for DB connection details"
  value       = aws_secretsmanager_secret.db_connection.arn
}

output "db_security_group_id" {
  description = "Security group protecting the Postgres instance"
  value       = aws_security_group.database.id
}
