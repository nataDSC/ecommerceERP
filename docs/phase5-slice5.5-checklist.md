# Phase 5 · Slice 5.5 — Observability & Operations Checklist

> **Goal:** Add lightweight, low-cost observability for the dev demo so we can
> see failures quickly, confirm the system is healthy, and react without having
> to inspect ECS manually every time.

---

## Current baseline already in place

The current AWS dev stack already provides a starting point:

- ECS task logs are being shipped to CloudWatch Logs.
- ALB, ECS, and RDS metrics already exist in CloudWatch.
- The app exposes a `/healthz` endpoint.
- GitHub Actions now automatically publishes and deploys the dev app.

Slice 5.5 builds on top of that baseline instead of starting from zero.

---

## Cost-conscious scope for the first implementation

Keep this slice intentionally small for dev/demo use:

1. **CloudWatch log retention tuning**
2. **One CloudWatch dashboard** for ALB + ECS + RDS health
3. **A few CloudWatch alarms** for the most important failures
4. **Optional SNS email notifications**
5. **A short runbook** for rollback and troubleshooting

Do **not** add X-Ray or complex tracing yet unless there is a clear need.

---

## AWS services needed

| Service              | Required?   | What we use it for                                          | Rough dev cost estimate                                      |
| -------------------- | ----------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| CloudWatch Logs      | Yes         | ECS API/UI logs, retention policy                           | Usually low; often $0–$5/month for a mostly idle demo        |
| CloudWatch Metrics   | Yes         | ALB, ECS, RDS health metrics                                | Basic AWS service metrics are generally already available    |
| CloudWatch Alarms    | Yes         | app-down / unhealthy-target / restart alerts                | Usually low; often a few dollars/month total for a small set |
| CloudWatch Dashboard | Recommended | single-pane demo status view                                | Low cost for one simple dashboard                            |
| SNS                  | Optional    | email alerts when alarms fire                               | Very low for occasional email notifications                  |
| X-Ray / tracing      | Not yet     | only add later if request-level debugging becomes necessary | Skip for now                                                 |

> **Practical dev expectation:** observability should stay much cheaper than the ALB, Fargate tasks, or RDS.

---

## Free Tier check before implementation

Before turning everything on, check these areas in Billing / Free Tier Explorer:

- CloudWatch Logs ingestion and storage
- CloudWatch alarms
- SNS email notifications

If the account still qualifies for Free Tier coverage, the cost impact may be even lower.

---

## Implementation steps

### Step 1 — Confirm log retention policy

**Why:** prevent logs from growing forever and adding unnecessary charges.

Checklist:

- [ ] Confirm the ECS log group exists for the dev stack
- [ ] Keep retention at 7–14 days for demo use
- [ ] Verify both API and UI containers are writing logs there
- [ ] Verify failed deployments still write enough logs for debugging

Suggested Terraform scope:

- reuse the existing CloudWatch log group already created by the ECS service module
- avoid creating separate log groups per task revision unless really needed

---

### Step 2 — Add a simple CloudWatch dashboard

**Why:** allow a fast visual health check without digging through multiple AWS pages.

Dashboard widgets to include:

- [ ] ALB request count
- [ ] ALB target 4xx/5xx count
- [ ] ALB unhealthy host count
- [ ] ECS service running task count
- [ ] ECS CPU utilization
- [ ] ECS memory utilization
- [ ] RDS CPU utilization
- [ ] RDS free storage space

Acceptance check:

- [ ] One dashboard exists and loads correctly in the console
- [ ] It shows both normal idle state and clear failure signals

---

### Step 3 — Add the first alarm set

**Why:** catch the most common demo outages automatically.

Recommended alarm set:

- [ ] **ALB unhealthy targets** — unhealthy host count greater than 0
- [ ] **ALB 5xx errors** — target 5xx count spikes above 0 over a short period
- [ ] **ECS running task count low** — running count below desired count
- [ ] **Optional RDS CPU alarm** — sustained high CPU usage
- [ ] **Optional RDS free storage alarm** — only if you expect heavier usage later

Keep the first version intentionally small to reduce noise.

---

### Step 4 — Optional SNS email notification path

**Why:** send a quick email when an alarm actually fires.

Checklist:

- [ ] Create one SNS topic for dev-demo alerts
- [ ] Add one email subscription
- [ ] Confirm the email subscription manually
- [ ] Attach only the high-value alarms to the topic
- [ ] Avoid alert fatigue by not wiring every metric to email

Validation:

- [ ] Trigger or simulate one alarm
- [ ] Confirm the notification email arrives
- [ ] Confirm the email subscription link was accepted manually

Example dev enablement variables:

```hcl
enable_observability_sns = true
observability_alert_email = "you@example.com"
```

---

### Step 5 — Add a short operational runbook

**Why:** make incident response easy during demo time.

Create a short doc/runbook covering:

- [ ] how to check the service URL health endpoint
- [ ] how to tail ECS logs
- [ ] how to see ECS service events
- [ ] how to force a new ECS deployment
- [ ] how to disable the stack for cost control
- [ ] how to re-enable the stack later

This can live in the repo as a compact markdown operational note.

Current runbook: [docs/aws-dev-operations-runbook.md](docs/aws-dev-operations-runbook.md)

---

## Recommended Terraform changes for this slice

When implementation starts, these are the likely repo touch points:

- `infra/terraform/modules/ecs-service/main.tf`
  - reuse or slightly extend the current CloudWatch log group settings
- `infra/terraform/environments/dev/main.tf`
  - wire dashboard, alarms, and optional SNS settings
- a new module if desired, such as:
  - `infra/terraform/modules/observability/`

For the first pass, keeping the resources in the dev environment or a small dedicated module is fine.

---

## Suggested low-cost defaults

Use these defaults for the first implementation:

- [ ] log retention = 7 days
- [ ] 1 dashboard only
- [ ] 3 primary alarms only
- [ ] 1 SNS topic and 1 email subscription max
- [ ] no X-Ray / tracing for now
- [ ] no third-party monitoring vendor yet

---

## Validation commands after implementation

```bash
# Health endpoint
curl -s "$(terraform output -raw service_url)/healthz"

# ECS service state
aws ecs describe-services \
  --cluster ecommerce-erp-dev \
  --services "$(terraform output -raw ecs_service_name)"

# Tail logs
aws logs tail "$(terraform output -raw cloudwatch_log_group_name)" --follow
```

Optional checks:

```bash
# List alarms
aws cloudwatch describe-alarms --query 'MetricAlarms[].AlarmName'

# List dashboards
aws cloudwatch list-dashboards
```

---

## Completion criteria

Slice 5.5 is complete when all of the following are true:

- [ ] ECS container logs are visible and retained for a sensible demo window
- [ ] One CloudWatch dashboard shows ALB + ECS + RDS health
- [ ] At least 3 high-value alarms exist and are easy to understand
- [ ] Optional SNS email notifications work end-to-end
- [ ] A short runbook exists for demo troubleshooting and recovery
- [ ] The cost impact remains small and acceptable for the dev account

---

## Recommendation for this repo

Implement this slice in **two mini-steps**:

1. **Step A:** dashboard + 3 alarms
2. **Step B:** SNS email + runbook

That gives strong value quickly while keeping risk and cost low.
