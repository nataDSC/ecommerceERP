set -euo pipefail

export AWS_DEFAULT_REGION=us-east-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export TF_STATE_BUCKET="ecommerce-erp-tfstate-${ACCOUNT_ID}"

cd /Users/nataliep/code/portfolio-projects/ecommerceERP/infra/terraform/environments/dev

echo "== Identity =="
aws sts get-caller-identity
echo "Region: ${AWS_DEFAULT_REGION}"
echo "State bucket: ${TF_STATE_BUCKET}"
echo

echo "== Current Terraform outputs =="
terraform output || true
echo

echo "== Destroy preview =="
terraform plan -destroy
echo

read -p "Type YES to destroy the current AWS stack: " CONFIRM
if [ "${CONFIRM}" != "YES" ]; then
  echo "Aborted."
  exit 1
fi

echo "== Destroying Terraform-managed stack =="
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
echo "✅ Stack destroy completed (or best-effort checked)"
