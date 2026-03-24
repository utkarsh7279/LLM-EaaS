#!/bin/bash

################################################################################
# LLM EaaS Production Deployment to AWS (ECS Fargate + RDS PostgreSQL)
# 
# Usage: bash deploy-aws-production.sh
# 
# Prerequisites:
#   - AWS CLI installed and configured (aws configure)
#   - Docker installed
#   - You have an AWS account with appropriate IAM permissions
#
# This script deploys the LLM EaaS application to AWS production.
################################################################################

set -e  # Exit on any error

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE VALUES
# ============================================================================

# AWS Region
AWS_REGION="us-east-1"

# AWS Account ID (get with: aws sts get-caller-identity --query Account)
AWS_ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID"

# Database Configuration
DB_INSTANCE_ID="llm-eaas-prod"
DB_INSTANCE_CLASS="db.t3.micro"
DB_MASTER_USER="postgres"
DB_MASTER_PASSWORD="$(openssl rand -base64 16)"  # Generate random password
DB_NAME="llm_eaas"
DB_ALLOCATED_STORAGE="20"

# Application Configuration
APP_NAME="llm-eaas"
ECR_BACKEND_REPO="llm-eaas-backend"
ECR_FRONTEND_REPO="llm-eaas-frontend"
ECS_CLUSTER_NAME="llm-eaas-prod"
ECS_SERVICE_NAME="llm-eaas-backend"
CONTAINER_PORT="8000"

# LLM Provider (ollama or openai)
LLM_PROVIDER="openai"
LLM_MODEL="gpt-4-mini"

# OpenAI API Key (required if using openai provider)
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# VPC Configuration (leave empty to use default VPC)
VPC_ID=""
SUBNET_IDS=""  # Space-separated, e.g., "subnet-xxxxx subnet-yyyyy"
SECURITY_GROUP_ID=""

# ============================================================================
# END CONFIGURATION
# ============================================================================

echo "=========================================="
echo "LLM EaaS AWS Production Deployment"
echo "=========================================="
echo ""
echo "AWS Region: $AWS_REGION"
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "Database: $DB_INSTANCE_ID"
echo "Application: $APP_NAME"
echo ""

# Validation
if [ "$AWS_ACCOUNT_ID" = "YOUR_AWS_ACCOUNT_ID" ]; then
    echo "ERROR: Please set AWS_ACCOUNT_ID in the script"
    exit 1
fi

if [ "$OPENAI_API_KEY" = "YOUR_OPENAI_API_KEY" ] && [ "$LLM_PROVIDER" = "openai" ]; then
    echo "ERROR: Please set OPENAI_API_KEY in the script"
    exit 1
fi

# ============================================================================
# STEP 1: Get Default VPC if not specified
# ============================================================================

echo ""
echo "[1/12] Getting VPC configuration..."

if [ -z "$VPC_ID" ]; then
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION)
    echo "Using default VPC: $VPC_ID"
fi

if [ -z "$SUBNET_IDS" ]; then
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[0:2].SubnetId' --output text --region $AWS_REGION)
    echo "Using subnets: $SUBNET_IDS"
fi

# ============================================================================
# STEP 2: Create Security Groups
# ============================================================================

echo ""
echo "[2/12] Creating security groups..."

# Create DB security group
DB_SG=$(aws ec2 create-security-group \
    --group-name llm-eaas-db-sg \
    --description "Security group for LLM EaaS RDS PostgreSQL" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || echo "sg-exists")

echo "Database security group: $DB_SG"

# Create ECS security group
ECS_SG=$(aws ec2 create-security-group \
    --group-name llm-eaas-ecs-sg \
    --description "Security group for LLM EaaS ECS tasks" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || echo "sg-exists")

echo "ECS security group: $ECS_SG"

# Allow traffic from ECS to DB
aws ec2 authorize-security-group-ingress \
    --group-id $DB_SG \
    --protocol tcp \
    --port 5432 \
    --source-security-group-id $ECS_SG \
    --region $AWS_REGION 2>/dev/null || echo "Ingress rule already exists"

# ============================================================================
# STEP 3: Create RDS PostgreSQL Database
# ============================================================================

echo ""
echo "[3/12] Creating RDS PostgreSQL database (this takes 5-10 minutes)..."

RDS_RESPONSE=$(aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_ID \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine postgres \
    --engine-version 16.1 \
    --master-username $DB_MASTER_USER \
    --master-user-password "$DB_MASTER_PASSWORD" \
    --allocated-storage $DB_ALLOCATED_STORAGE \
    --storage-type gp3 \
    --db-name $DB_NAME \
    --backup-retention-period 7 \
    --multi-az false \
    --publicly-accessible false \
    --db-subnet-group-name default \
    --vpc-security-group-ids $DB_SG \
    --region $AWS_REGION \
    --query 'DBInstance.Endpoint.Address' --output text 2>/dev/null || echo "DB already exists")

echo "Database created: $RDS_RESPONSE"

# Wait for DB availability
echo "Waiting for database to be available..."
for i in {1..60}; do
    STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier $DB_INSTANCE_ID \
        --region $AWS_REGION \
        --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "creating")
    
    if [ "$STATUS" = "available" ]; then
        echo "Database is available!"
        break
    fi
    
    echo "Status: $STATUS... waiting (${i}/60)"
    sleep 10
done

# Get DB endpoint
DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_ID \
    --region $AWS_REGION \
    --query 'DBInstances[0].Endpoint.Address' --output text)

DB_URL="postgresql+asyncpg://$DB_MASTER_USER:$DB_MASTER_PASSWORD@$DB_ENDPOINT:5432/$DB_NAME"
echo "Database endpoint: $DB_ENDPOINT"

# ============================================================================
# STEP 4: Create ECR Repositories
# ============================================================================

echo ""
echo "[4/12] Creating ECR repositories..."

# Backend repo
aws ecr create-repository \
    --repository-name $ECR_BACKEND_REPO \
    --region $AWS_REGION \
    --query 'repository.repositoryUri' --output text 2>/dev/null || echo "Repo exists"

# Frontend repo
aws ecr create-repository \
    --repository-name $ECR_FRONTEND_REPO \
    --region $AWS_REGION \
    --query 'repository.repositoryUri' --output text 2>/dev/null || echo "Repo exists"

echo "ECR repositories created"

# ============================================================================
# STEP 5: Build and Push Docker Images
# ============================================================================

echo ""
echo "[5/12] Building and pushing Docker images..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend
echo "Building backend image..."
cd "$(dirname "$0")/backend"
docker build -t $ECR_BACKEND_REPO:latest .
docker tag $ECR_BACKEND_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO:latest
echo "Backend image pushed"

# Build and push frontend
echo "Building frontend image..."
cd "$(dirname "$0")/frontend"
docker build -t $ECR_FRONTEND_REPO:latest .
docker tag $ECR_FRONTEND_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_FRONTEND_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_FRONTEND_REPO:latest
echo "Frontend image pushed"

cd "$(dirname "$0")"

# ============================================================================
# STEP 6: Create CloudWatch Log Group
# ============================================================================

echo ""
echo "[6/12] Creating CloudWatch log group..."

aws logs create-log-group \
    --log-group-name /ecs/$APP_NAME \
    --region $AWS_REGION 2>/dev/null || echo "Log group already exists"

# ============================================================================
# STEP 7: Create IAM Execution Role
# ============================================================================

echo ""
echo "[7/12] Creating IAM execution role..."

ASSUME_ROLE_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
)

aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document "$ASSUME_ROLE_POLICY" \
    --region $AWS_REGION 2>/dev/null || echo "Role already exists"

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
    --region $AWS_REGION 2>/dev/null || echo "Policy already attached"

# Attach Secrets Manager policy
SECRETS_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:llm-eaas/*"
    }
  ]
}
EOF
)

aws iam put-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-name ECSSecretsPolicy \
    --policy-document "$SECRETS_POLICY" \
    --region $AWS_REGION 2>/dev/null || echo "Secrets policy already attached"

# ============================================================================
# STEP 8: Store Secrets in AWS Secrets Manager
# ============================================================================

echo ""
echo "[8/12] Storing secrets in AWS Secrets Manager..."

# Store database URL
aws secretsmanager create-secret \
    --name llm-eaas/database-url \
    --secret-string "$DB_URL" \
    --region $AWS_REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id llm-eaas/database-url \
    --secret-string "$DB_URL" \
    --region $AWS_REGION

echo "Database URL stored in Secrets Manager"

# Store OpenAI API Key
aws secretsmanager create-secret \
    --name llm-eaas/openai-api-key \
    --secret-string "$OPENAI_API_KEY" \
    --region $AWS_REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id llm-eaas/openai-api-key \
    --secret-string "$OPENAI_API_KEY" \
    --region $AWS_REGION

echo "OpenAI API Key stored in Secrets Manager"

# ============================================================================
# STEP 9: Create ECS Cluster
# ============================================================================

echo ""
echo "[9/12] Creating ECS cluster..."

aws ecs create-cluster \
    --cluster-name $ECS_CLUSTER_NAME \
    --region $AWS_REGION \
    --query 'cluster.clusterArn' --output text 2>/dev/null || echo "Cluster already exists"

echo "ECS cluster created: $ECS_CLUSTER_NAME"

# ============================================================================
# STEP 10: Register ECS Task Definition
# ============================================================================

echo ""
echo "[10/12] Registering ECS task definition..."

TASK_DEFINITION=$(cat <<EOF
{
  "family": "$APP_NAME",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "$APP_NAME",
      "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_BACKEND_REPO:latest",
      "portMappings": [
        {
          "containerPort": $CONTAINER_PORT,
          "hostPort": $CONTAINER_PORT,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LLM_EAAS_LLM_PROVIDER",
          "value": "$LLM_PROVIDER"
        },
        {
          "name": "LLM_EAAS_LLM_MODEL",
          "value": "$LLM_MODEL"
        },
        {
          "name": "LLM_EAAS_REGRESSION_THRESHOLD",
          "value": "0.05"
        },
        {
          "name": "LLM_EAAS_JUDGE_TEMPERATURE_DEFAULT",
          "value": "0.2"
        }
      ],
      "secrets": [
        {
          "name": "LLM_EAAS_DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:llm-eaas/database-url"
        },
        {
          "name": "LLM_EAAS_LLM_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:llm-eaas/openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$APP_NAME",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:$CONTAINER_PORT/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF
)

echo "$TASK_DEFINITION" > /tmp/task-definition.json

aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-definition.json \
    --region $AWS_REGION \
    --query 'taskDefinition.taskDefinitionArn' --output text

echo "Task definition registered"

# ============================================================================
# STEP 11: Create ECS Service
# ============================================================================

echo ""
echo "[11/12] Creating ECS service..."

SUBNET_ARRAY=($SUBNET_IDS)

aws ecs create-service \
    --cluster $ECS_CLUSTER_NAME \
    --service-name $ECS_SERVICE_NAME \
    --task-definition $APP_NAME \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_ARRAY[0]},${SUBNET_ARRAY[1]}],securityGroups=[$ECS_SG],assignPublicIp=ENABLED}" \
    --region $AWS_REGION \
    --query 'service.serviceArn' --output text 2>/dev/null || echo "Service already exists"

echo "ECS service created"

# ============================================================================
# STEP 12: Deployment Summary
# ============================================================================

echo ""
echo "=========================================="
echo "Deployment Successful!"
echo "=========================================="
echo ""
echo "Deployment Details:"
echo "  Cluster: $ECS_CLUSTER_NAME"
echo "  Service: $ECS_SERVICE_NAME"
echo "  Region: $AWS_REGION"
echo "  Database: $DB_ENDPOINT"
echo ""
echo "Useful Commands:"
echo ""
echo "View service status:"
echo "  aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services $ECS_SERVICE_NAME --region $AWS_REGION"
echo ""
echo "View task logs:"
echo "  aws logs tail /ecs/$APP_NAME --follow --region $AWS_REGION"
echo ""
echo "Scale service (change 2 to desired count):"
echo "  aws ecs update-service --cluster $ECS_CLUSTER_NAME --service $ECS_SERVICE_NAME --desired-count 2 --region $AWS_REGION"
echo ""
echo "Get running tasks:"
echo "  aws ecs list-tasks --cluster $ECS_CLUSTER_NAME --service-name $ECS_SERVICE_NAME --region $AWS_REGION"
echo ""
echo "View task details:"
echo "  aws ecs describe-tasks --cluster $ECS_CLUSTER_NAME --tasks <TASK_ARN> --region $AWS_REGION"
echo ""
echo "Database Connection String:"
echo "  $DB_URL"
echo ""
echo "Next Steps:"
echo "  1. Wait 2-3 minutes for tasks to start"
echo "  2. Check CloudWatch logs for startup errors"
echo "  3. Get the ALB DNS name to test the API"
echo "  4. Run: curl http://<ALB_DNS>/health"
echo ""
