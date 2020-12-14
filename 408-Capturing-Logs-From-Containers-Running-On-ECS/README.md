# 408 Capturing Logs From Containers Running On ECS

## In the root of the AWS Cookbook repo cd to the cdk folder for this recipe
cd Chapter4/408-Capturing-Logs-From-Containers-Running-On-ECS/cdk-AWSCookbook-408

## Activate the python virtual environment
source .venv/bin/activate

## Install the Python modules
python -m pip install -r requirements.txt

## Deploy the stack 
cdk deploy

## Create the ECS service-linked role if it does not exist:
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com

## Create an IAM role using the statement in the file provided
aws iam create-role --role-name AWSCookbook408ECS --assume-role-policy-document file://task-execution-assume-role.json

## Attach the AWS provided managed policy for ECS Task Execution to the role that we just created 
aws iam attach-role-policy --role-name AWSCookbook408ECS --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

## Create a Log Group in CloudWatch 
aws logs create-log-group --log-group-name AWSCookbook408ECS

## Create the ECS task using the config and associate the IAM role. 
aws ecs register-task-definition --execution-role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/AWSCookbook408ECS" --cli-input-json file://taskdef.json

## Run the ECS task on the ECS Cluster that we created earlier in this recipe with the CDK.
aws ecs run-task --cluster <<ECSClusterName>> --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[<<VPCPublicSubnets>>],securityGroups=[<<VPCDefaultSecurityGroup>>],assignPublicIp=ENABLED}" --task-definition awscookbook408:1

## Check the status of the task
aws ecs list-tasks --cluster <<ECSClusterName>>

## Then use the Task ARN to check for the “RUNNING” state with the describe-tasks command output
aws ecs describe-tasks --cluster <<ECSClusterName>> --tasks <<TaskARN>>

## After the task has reached the “RUNNING” state (approximately 15 seconds), use the following commands to view logs. 
aws logs describe-log-streams --log-group-name AWSCookbook408ECS

## Note the log stream name from abobe anad get-log-events
aws logs get-log-events --log-group-name AWSCookbook408ECS --log-stream-name <<logStreamName>>

## Clean Up

## Stop the ECS Task
aws ecs stop-task --cluster <<ECSClusterName>> --task <<TaskARN>>

## Delete the IAM Policy Attachment and Role
aws iam detach-role-policy --role-name AWSCookbook408ECS --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam delete-role --role-name AWSCookbook408ECS

## Delete Log Group
aws logs delete-log-group --log-group-name awscookbook

## CD to the cdk folder for this recipe and remove the resources created by the CDK

cd cdk-AWSCookbook-408/
cdk destroy

## Deactivate the Python Virtual Environment
deactivate
