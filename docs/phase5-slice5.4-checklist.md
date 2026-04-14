# Phase 5 · Slice 5.4 — Edge Security Checklist

> Goal: add low-friction edge protections to the current public AWS URL without requiring a custom domain.

---

## Scope for the first pass

Keep the initial security layer small and practical:

1. Add a regional AWS WAF web ACL to the existing ALB
2. Enable a few AWS-managed protections
3. Add a simple per-IP rate limit rule
4. Keep ALB ingress CIDR controls configurable for later tightening

---

## Baseline protections included

- AWS managed IP reputation list
- AWS managed common web exploit protections
- AWS managed known bad inputs rules
- Per-IP rate limiting
- Optional ALB ingress CIDR restriction through Terraform variables

---

## Why no custom domain is required

AWS WAF attaches to the ALB itself, so it protects the current AWS hostname as-is.
A custom domain is only needed later for branding and custom HTTPS certificates.

---

## Suggested validation after apply

```bash
cd infra/terraform/environments/dev
terraform output waf_web_acl_name
terraform output service_url
```

Optional CLI check:

```bash
export AWS_PROFILE=alex-aws
export AWS_DEFAULT_REGION=us-east-1

aws wafv2 list-web-acls --scope REGIONAL
```

---

## Cost note

WAF is not free, so keep the first policy small and only enable the rules that add obvious value for the public demo.
