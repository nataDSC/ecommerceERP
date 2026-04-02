export AWS_DEFAULT_REGION=us-east-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export TF_STATE_BUCKET="ecommerce-erp-tfstate-${ACCOUNT_ID}"

python - <<'PY'
import json, subprocess, os, sys

bucket = os.environ["TF_STATE_BUCKET"]

result = subprocess.run(
    ["aws", "s3api", "list-object-versions", "--bucket", bucket, "--output", "json"],
    capture_output=True,
    text=True,
    check=True,
)

data = json.loads(result.stdout or "{}")
objects = []

for item in data.get("Versions", []):
    objects.append({"Key": item["Key"], "VersionId": item["VersionId"]})

for item in data.get("DeleteMarkers", []):
    objects.append({"Key": item["Key"], "VersionId": item["VersionId"]})

if objects:
    delete_payload = json.dumps({"Objects": objects, "Quiet": True})
    subprocess.run(
        ["aws", "s3api", "delete-objects", "--bucket", bucket, "--delete", delete_payload],
        check=True,
    )
    print(f"Deleted {len(objects)} versioned objects/delete markers from {bucket}")
else:
    print(f"No remaining object versions in {bucket}")
PY

aws s3api delete-bucket --bucket "${TF_STATE_BUCKET}"

