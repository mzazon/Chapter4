# Chapter 4
## Setup your environment
### Set your default region 
  export AWS_REGION=us-east-1
### Set your AWS ACCOUNT ID 
  export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
### Validate AWS Cli Setup and access
  aws ec2 describe-instances
