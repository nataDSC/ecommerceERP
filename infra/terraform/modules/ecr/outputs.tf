output "repository_url" {
  description = "Full ECR repository URL used for docker push/pull"
  value       = aws_ecr_repository.api.repository_url
}

output "repository_arn" {
  description = "ECR repository ARN (used in IAM policies)"
  value       = aws_ecr_repository.api.arn
}
