# ──────────────────────────────────────────────────────────────
# MedAI Cloud Deployment Guide
# AWS ECS (Fargate) + ECR + ALB + RDS (optional)
# ──────────────────────────────────────────────────────────────

# ── 1. Build & Push Docker image to AWS ECR ──────────────────
# Replace <ACCOUNT> and <REGION> with your values.

# Login to ECR
aws ecr get-login-password --region <REGION> \
  | docker login --username AWS \
    --password-stdin <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com

# Create repository
aws ecr create-repository --repository-name medai-diagnostics

# Build image
docker build -t medai-diagnostics .

# Tag & push
docker tag medai-diagnostics:latest \
  <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/medai-diagnostics:latest
docker push <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/medai-diagnostics:latest


# ── 2. ECS Task Definition (task-definition.json) ────────────
# {
#   "family": "medai-task",
#   "networkMode": "awsvpc",
#   "requiresCompatibilities": ["FARGATE"],
#   "cpu": "1024",
#   "memory": "2048",
#   "executionRoleArn": "arn:aws:iam::<ACCOUNT>:role/ecsTaskExecutionRole",
#   "containerDefinitions": [{
#     "name": "medai",
#     "image": "<ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/medai-diagnostics:latest",
#     "portMappings": [{"containerPort": 8080}],
#     "environment": [
#       {"name": "SECRET_KEY", "value": "<STRONG-RANDOM-SECRET>"}
#     ],
#     "logConfiguration": {
#       "logDriver": "awslogs",
#       "options": {
#         "awslogs-group": "/ecs/medai",
#         "awslogs-region": "<REGION>",
#         "awslogs-stream-prefix": "ecs"
#       }
#     }
#   }]
# }


# ── 3. Create ECS Service (Fargate) ─────────────────────────
# aws ecs create-service \
#   --cluster medai-cluster \
#   --service-name medai-service \
#   --task-definition medai-task \
#   --desired-count 2 \
#   --launch-type FARGATE \
#   --network-configuration "awsvpcConfiguration={
#     subnets=[subnet-xxx,subnet-yyy],
#     securityGroups=[sg-xxx],
#     assignPublicIp=ENABLED}"


# ── 4. Google Cloud Run (Alternative) ────────────────────────
# gcloud builds submit --tag gcr.io/<PROJECT>/medai-diagnostics
# gcloud run deploy medai \
#   --image gcr.io/<PROJECT>/medai-diagnostics \
#   --platform managed \
#   --region us-central1 \
#   --memory 2Gi \
#   --cpu 2 \
#   --set-env-vars SECRET_KEY=<SECRET>


# ── 5. Azure Container Apps (Alternative) ────────────────────
# az containerapp create \
#   --name medai \
#   --resource-group medai-rg \
#   --image medai-diagnostics:latest \
#   --cpu 1 --memory 2Gi \
#   --env-vars SECRET_KEY=<SECRET>


# ── SECURITY CHECKLIST ────────────────────────────────────────
# [ ] SECRET_KEY set via environment variable (not hardcoded)
# [ ] HTTPS enforced via ALB/CloudFront/load balancer TLS cert
# [ ] VPC private subnet for app; only ALB exposed publicly
# [ ] S3 bucket for model artifacts (replace joblib local files)
# [ ] CloudWatch log retention = 90 days (HIPAA minimum)
# [ ] WAF rules on ALB for OWASP Top 10
# [ ] Secrets Manager for any credentials
# [ ] IAM least-privilege roles
# [ ] Enable VPC Flow Logs
# [ ] RDS (if used) encrypted at rest (AES-256) + in transit (TLS)
# [ ] Enable AWS CloudTrail for API audit
# [ ] S3 bucket versioning + lifecycle policy for audit logs
# [ ] Backup: daily automated snapshots, 30-day retention
