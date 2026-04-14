#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_DIR="$(cd "${SCRIPT_DIR}/../environments/dev" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

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

cd "${ROOT_DIR}"

echo "== Identity =="
aws sts get-caller-identity
echo "Region: ${AWS_DEFAULT_REGION}"
echo "State bucket: ${TF_STATE_BUCKET}"
echo

echo "== Publishing latest AWS-compatible image =="
./scripts/push-ecr-image

echo
cd "${DEV_DIR}"

echo "== Terraform init check =="
terraform init -input=false >/dev/null

echo "== Terraform apply =="
terraform apply -auto-approve

echo
if aws ecs describe-services --cluster ecommerce-erp-dev --services ecommerce-erp-api-dev ecommerce-erp-ui-dev >/dev/null 2>&1; then
  echo "== Waiting for ECS services to stabilize =="
  aws ecs wait services-stable --cluster ecommerce-erp-dev --services ecommerce-erp-api-dev ecommerce-erp-ui-dev
fi

echo
SERVICE_URL="$(terraform output -raw service_url)"
echo "Service URL: ${SERVICE_URL}"
echo "UI URL: ${SERVICE_URL}"
echo "Health check: ${SERVICE_URL}/healthz"

echo
curl -fsS "${SERVICE_URL}/healthz" || true
echo

echo "Deploy complete."
