#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_DIR="$(cd "${SCRIPT_DIR}/../environments/dev" && pwd)"

export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

if [[ -n "${AWS_PROFILE:-}" ]]; then
  echo "== Exporting credentials for AWS_PROFILE=${AWS_PROFILE} =="
  if CREDS="$(aws configure export-credentials --profile "${AWS_PROFILE}" --format env 2>/dev/null)"; then
    eval "${CREDS}"
  else
    echo "Warning: could not export credentials from AWS_PROFILE; continuing with current shell environment." >&2
  fi
fi

export ACCOUNT_ID="${ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
export TF_STATE_BUCKET="${TF_STATE_BUCKET:-ecommerce-erp-tfstate-${ACCOUNT_ID}}"

cd "${DEV_DIR}"

echo "== Identity =="
aws sts get-caller-identity
echo "Region: ${AWS_DEFAULT_REGION}"
echo "State bucket: ${TF_STATE_BUCKET}"
echo "Terraform dir: ${DEV_DIR}"
echo

echo "== Terraform init check =="
terraform init -input=false >/dev/null
echo

echo "== Current Terraform outputs =="
terraform output || true
echo

echo "== Destroy preview =="
terraform plan -destroy
echo

if [[ "${AUTO_APPROVE_DESTROY:-0}" == "1" ]]; then
  CONFIRM="YES"
else
  read -r -p "Type YES to destroy the current AWS demo stack: " CONFIRM
fi

if [[ "${CONFIRM}" != "YES" ]]; then
  echo "Aborted."
  exit 1
fi

echo "== Destroying Terraform-managed demo stack =="
terraform destroy -auto-approve
echo

echo "== Post-destroy checks =="
aws rds describe-db-instances \
  --query 'DBInstances[].DBInstanceIdentifier' || true

aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[].LoadBalancerName' || true

aws ecs describe-clusters \
  --clusters ecommerce-erp-dev \
  --query 'clusters[].{name:clusterName,status:status}' || true

aws ecr describe-repositories \
  --repository-names ecommerce-erp \
  --query 'repositories[].repositoryName' || true

echo
echo "Stack destroy completed. The remote Terraform backend remains so you can re-apply later."
