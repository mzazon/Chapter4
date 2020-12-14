# Using AutoScaling with Containers
## Preparation
cd 406-Autoscaling-Container-Workloads/cdk-AWS-Cookbook-406/
python3 -m venv .env
source .env/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt --no-dependencies
cdk deploy

## Steps

### Get the URL of the ECS Service
aws cloudformation describe-stacks --stack-name AWSCookbook-406 --query "Stacks[0].Outputs[0].OutputValue" --output text

## cURL to the URL
curl -v -m 10 <<ServiceURL>>

## Trigger the CPU Load Test
curl -v -m 10 <<ServiceURL>>/cpu

### Clean Up

