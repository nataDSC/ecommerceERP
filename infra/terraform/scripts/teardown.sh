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

echo "== Terraform-managed resources in state =="
terraform state list || true
echo

echo "== Destroy preview =="
terraform plan -destroy || true
echo

read -p "Type YES to destroy Terraform-managed AWS resources: " CONFIRM
if [ "${CONFIRM}" != "YES" ]; then
  echo "Aborted."
  exit 1
fi

echo "== First destroy attempt =="
terraform destroy -auto-approve || true
echo

echo "== If ECR repo still has images, remove them =="
if aws ecr describe-repositories --repository-names ecommerce-erp >/dev/null 2>&1; then
  IMAGE_IDS=$(aws ecr list-images --repository-name ecommerce-erp --query 'imageIds' --output json)
  if [ "${IMAGE_IDS}" != "[]" ]; then
    aws ecr batch-delete-image --repository-name ecommerce-erp --image-ids "${IMAGE_IDS}" || true
  fi
fi
echo

echo "== Second destroy attempt (cleanup retry) =="
terraform destroy -auto-approve || true
echo

echo "== Post-destroy checks =="
aws ec2 describe-nat-gateways \
  --filter Name=state,Values=available,pending,deleting Name=vpc-id,Values=vpc-0d13c95c374c2b1b1 \
  --query 'NatGateways[].{NatGatewayId:NatGatewayId,State:State}' || true

aws ec2 describe-vpcs --vpc-ids vpc-0d13c95c374c2b1b1 \
  --query 'Vpcs[].{VpcId:VpcId,State:State}' || true

aws ecs describe-clusters --clusters ecommerce-erp-dev \
  --query 'clusters[].{name:clusterName,status:status}' || true

aws ecr describe-repositories --repository-names ecommerce-erp \
  --query 'repositories[].repositoryName' || true
echo

read -p "Also delete Terraform backend resources (S3 state bucket + DynamoDB lock table)? Type DELETE_BACKEND to continue: " BACKEND_CONFIRM
if [ "${BACKEND_CONFIRM}" = "DELETE_BACKEND" ]; then
  echo "== Deleting DynamoDB lock table =="
  aws dynamodb delete-table --table-name ecommerce-erp-tflock || true

  echo "== Emptying and deleting S3 state bucket =="
  aws s3 rm "s3://${TF_STATE_BUCKET}" --recursive || true
  aws s3api delete-bucket --bucket "${TF_STATE_BUCKET}" || true
fi

echo
echo "✅ Teardown flow finished"

