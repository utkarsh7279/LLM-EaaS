# AWS Production Deployment Guide

This guide walks you through deploying LLM EaaS to AWS production using the automated deployment script.

## Prerequisites

1. **AWS Account** with sufficient permissions (admin or EC2, RDS, ECS, IAM, Secrets Manager, CloudWatch, ECR permissions)
2. **AWS CLI** installed: `brew install awscli` (macOS) or `apt-get install awscli` (Linux)
3. **Docker** installed and running
4. **AWS Credentials** configured: `aws configure`

## Quick Start (15 minutes setup + 10 minutes deployment time)

### 1. Get Your AWS Account ID

```bash
aws sts get-caller-identity --query Account --output text
# Output: 123456789012
```

Copy this number - you'll need it.

### 2. Get Your OpenAI API Key

If using OpenAI (recommended for production):
- Go to https://platform.openai.com/api-keys
- Create a new secret key
- Copy it (you'll need it in step 3)

### 3. Edit the Deployment Script

```bash
cd /Users/utkarshraj/LLM\ EaaS
nano deploy-aws-production.sh
```

Update these values at the top of the script:

```bash
AWS_ACCOUNT_ID="123456789012"           # Your AWS Account ID from step 1
OPENAI_API_KEY="sk-proj-xxxxx..."       # Your OpenAI API key
DB_MASTER_PASSWORD="secure-password"    # Set a secure database password
```

Save and exit (Ctrl+X, then Y, then Enter in nano).

### 4. Make Script Executable

```bash
chmod +x deploy-aws-production.sh
```

### 5. Run the Deployment Script

```bash
./deploy-aws-production.sh
```

The script will:
- Create RDS PostgreSQL database (5-10 min)
- Set up ECR repositories
- Build and push Docker images
- Create ECS cluster and service
- Configure security groups
- Store secrets safely

**Total time: ~15-20 minutes**

### 6. Monitor Deployment

While the script runs, you can monitor in another terminal:

```bash
# Watch ECS service status
watch -n 5 'aws ecs describe-services --cluster llm-eaas-prod --services llm-eaas-backend --region us-east-1 --query "services[0].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount}"'

# Watch CloudWatch logs
aws logs tail /ecs/llm-eaas --follow --region us-east-1
```

### 7. Verify Deployment

Once tasks are running (check CloudWatch logs):

```bash
# Get the IP of a running task
TASK=$(aws ecs list-tasks --cluster llm-eaas-prod --region us-east-1 --query 'taskArns[0]' --output text)

aws ecs describe-tasks --cluster llm-eaas-prod --tasks $TASK --region us-east-1 --query 'tasks[0].attachments[?name==`ElasticNetworkInterface`].details[?name==`privateIpv4Address`].value' --output text

# Test health endpoint (replace with actual IP)
curl http://<TASK_IP>:8000/health
# Expected output: {"status":"ok"}
```

## Troubleshooting

### Tasks Not Starting

Check logs:
```bash
aws logs tail /ecs/llm-eaas --follow --region us-east-1
```

Common issues:
- **ImageNotFound**: Docker build didn't push successfully - re-run script
- **SecretNotFound**: Secrets Manager credentials failed - verify API key
- **DBConnectionError**: Database not ready yet - wait 10 more minutes

### Database Not Available

```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier llm-eaas-prod --region us-east-1 --query 'DBInstances[0].DBInstanceStatus'
```

Should show `available`. If `creating`, wait 5 more minutes.

### Can't Push to ECR

```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

## Cost Estimation (US East 1, per month)

- **RDS PostgreSQL db.t3.micro**: ~$12
- **ECS Fargate (2 tasks × 512 CPU/1GB RAM)**: ~$15
- **Data transfer**: ~$5
- **Secrets Manager**: Free (1 secret)
- **CloudWatch Logs**: ~$2

**Total: ~$34/month** for a small production deployment.

## Switching to Ollama (Free, Local LLM)

To use Ollama instead of OpenAI:

1. Edit the script:
```bash
nano deploy-aws-production.sh
```

2. Change:
```bash
LLM_PROVIDER="ollama"
LLM_MODEL="llama3.2"
```

3. Remove the OpenAI API key requirement (comment out the validation)

4. Re-run the script

Note: You'll need to deploy Ollama on EC2 or manage it separately.

## Updating Your Application

After making code changes:

1. Commit to GitHub
2. Run the deployment script again (it will rebuild and push new images)
3. Update ECS service:

```bash
aws ecs update-service \
  --cluster llm-eaas-prod \
  --service llm-eaas-backend \
  --force-new-deployment \
  --region us-east-1
```

## Advanced: Add Load Balancer

For high availability, add an Application Load Balancer:

```bash
# Create target group
aws elbv2 create-target-group \
  --name llm-eaas-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id <VPC_ID> \
  --health-check-enabled \
  --health-check-path /health \
  --region us-east-1

# Create load balancer
aws elbv2 create-load-balancer \
  --name llm-eaas-alb \
  --subnets <SUBNET_ID_1> <SUBNET_ID_2> \
  --security-groups <SECURITY_GROUP_ID> \
  --region us-east-1
```

## Cleanup (Delete Everything)

To remove all AWS resources and stop charges:

```bash
# Delete ECS service
aws ecs delete-service --cluster llm-eaas-prod --service llm-eaas-backend --force --region us-east-1

# Delete ECS cluster
aws ecs delete-cluster --cluster llm-eaas-prod --region us-east-1

# Delete RDS database
aws rds delete-db-instance --db-instance-identifier llm-eaas-prod --skip-final-snapshot --region us-east-1

# Delete ECR repositories
aws ecr delete-repository --repository-name llm-eaas-backend --force --region us-east-1
aws ecr delete-repository --repository-name llm-eaas-frontend --force --region us-east-1

# Delete CloudWatch log group
aws logs delete-log-group --log-group-name /ecs/llm-eaas --region us-east-1

# Delete secrets
aws secretsmanager delete-secret --secret-id llm-eaas/database-url --force-delete-without-recovery --region us-east-1
aws secretsmanager delete-secret --secret-id llm-eaas/openai-api-key --force-delete-without-recovery --region us-east-1
```

## Support

For deployment issues:
1. Check CloudWatch logs: `aws logs tail /ecs/llm-eaas --follow --region us-east-1`
2. Review DEPLOYMENT_GUIDE.md in the repository
3. Check TROUBLESHOOTING.md for common issues
