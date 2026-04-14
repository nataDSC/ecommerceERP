output "web_acl_arn" {
  description = "ARN of the AWS WAF web ACL protecting the ALB"
  value       = var.create_waf ? aws_wafv2_web_acl.this[0].arn : null
}

output "web_acl_name" {
  description = "Name of the AWS WAF web ACL protecting the ALB"
  value       = var.create_waf ? aws_wafv2_web_acl.this[0].name : null
}
