locals {
  name_prefix = "ecommerce-erp-${var.environment}"

  common_tags = {
    Project     = "ecommerce-erp"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_wafv2_web_acl" "this" {
  count = var.create_waf ? 1 : 0

  name        = "${local.name_prefix}-waf"
  description = "Baseline regional WAF protections for the ecommerce-erp ${var.environment} ALB"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf"
    sampled_requests_enabled   = true
  }

  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 10

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-ip-reputation"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 20

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-common"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 30

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-known-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitPerIp"
    priority = 40

    action {
      block {}
    }

    statement {
      rate_based_statement {
        aggregate_key_type = "IP"
        limit              = var.rate_limit_per_5_minutes
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  tags = local.common_tags
}

resource "aws_wafv2_web_acl_association" "alb" {
  count = var.create_waf ? 1 : 0

  resource_arn = var.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.this[0].arn
}
