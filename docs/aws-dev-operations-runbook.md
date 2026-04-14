# AWS Dev Operations Runbook

This runbook is for the dev demo stack running in AWS.
Use it for quick health checks, deployment verification, troubleshooting, and cost control.

---

## 1. Verify the app is healthy

```bash
cd infra/terraform/environments/dev
curl -s "$(terraform output -raw service_url)/healthz"
```

Expected response:

```json
{"status":"ok"}
```

---

## 2. Check ECS service status

```bash
export AWS_PROFILE=alex-aws
export AWS_DEFAULT_REGION=us-east-1

aws ecs describe-services \
  --cluster ecommerce-erp-dev \
  --services ecommerce-erp-api-dev ecommerce-erp-ui-dev \
  --query 'services[].{name:serviceName,desired:desiredCount,running:runningCount,pending:pendingCount,status:status}'
```

What to look for:

- `running` should match `desired`
- `pending` should usually be `0`
- `status` should be `ACTIVE`

---

## 3. Tail application logs

```bash
cd infra/terraform/environments/dev
export AWS_PROFILE=alex-aws
export AWS_DEFAULT_REGION=us-east-1

aws logs tail "$(terraform output -raw cloudwatch_log_group_name)" --follow
```

Use this during:

- fresh deployments
- task startup failures
- API error investigation
- UI loading issues

---

## 4. Check recent ECS service events

```bash
export AWS_PROFILE=alex-aws
export AWS_DEFAULT_REGION=us-east-1

aws ecs describe-services \
  --cluster ecommerce-erp-dev \
  --services ecommerce-erp-api-dev \
  --query 'services[0].events[0:10]'
```

This is the fastest place to spot:

- failed task launches
- image pull problems
- health-check failures
- secrets access errors

---

## 5. Force a new deployment

```bash
export AWS_PROFILE=alex-aws
export AWS_DEFAULT_REGION=us-east-1

aws ecs update-service \
  --cluster ecommerce-erp-dev \
  --service ecommerce-erp-api-dev \
  --force-new-deployment

aws ecs update-service \
  --cluster ecommerce-erp-dev \
  --service ecommerce-erp-ui-dev \
  --force-new-deployment
```

Use this after:

- pushing a new image manually
- clearing a stuck task state
- refreshing the running revision

---

## 6. Re-enable the full demo stack

```bash
export AWS_PROFILE=alex-aws
export AWS_DEFAULT_REGION=us-east-1
bash infra/terraform/scripts/deploy-stack-53.sh
```

This will:

- bootstrap ECR if needed
- push the latest AWS-compatible image
- run Terraform apply
- wait for ECS to stabilize

---

## 7. Disable the stack for cost control

```bash
export AWS_PROFILE=alex-aws
export AWS_DEFAULT_REGION=us-east-1
bash infra/terraform/scripts/destroy-stack-52.sh
```

Use this for long idle periods when you want to minimize charges.

---

## 8. Check the observability resources

```bash
cd infra/terraform/environments/dev
terraform output observability_dashboard_name
terraform output observability_alarm_names
```

Current Step A observability includes:

- one CloudWatch dashboard
- ALB unhealthy host alarm
- ALB target 5xx alarm
- ECS API running-task-count alarm

---

## 9. Common quick diagnosis flow

If the app looks down:

1. hit `/healthz`
2. check ECS service counts
3. inspect ECS events
4. tail CloudWatch logs
5. force a new deployment if needed

That sequence usually identifies the problem quickly.
