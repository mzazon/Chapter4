# Launching a Fargate container task in response to an event

## Clone this repo and folder
git clone https://github.com/johnculkin/AWSCookBook
## CD to this recipe
cd Chapter4/407-Fargate-Task-With-Event

## CD to the CDK Folder 
cd cdk-Fargate-Task-With-Event
## Create a virtual Python environment
python -m venv .venv

## Activate the python virtual environment
source .venv/bin/activate

## Install the Python modules
python -m pip install -r requirements.txt

## Deploy the stack (Outputs will be provided)
cdk deploy

## Create and set an enviroment variable for the bucketname - Ex
export BUCKET_NAME="<<S3BucketName>>"

## Modify the value in bucketpolicy-template.json and create a bucketpolicy.json for use
sed -e "s/AWS_ACCOUNT_ID/${AWS_ACCOUNT_ID}/g" -e "s/BUCKET_NAME/${BUCKET_NAME}/g" bucketpolicy-template.json > bucketpolicy.json

## Update bucketpolicy.json
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucketpolicy.json

## Create a CloudTrail trail and activate the trail
aws cloudtrail create-trail --name awscookbook-trail --s3-bucket-name $BUCKET_NAME
aws cloudtrail start-logging --name awscookbook-trail

## Configure CloudTrail to log events on our S3 bucket, so that we can use CloudWatch Events later
aws cloudtrail put-event-selectors --trail-name awscookbook-trail --event-selectors '[{ "ReadWriteType": "WriteOnly", "IncludeManagementEvents":false, "DataResources": [{ "Type": "AWS::S3::Object", "Values": ["arn:aws:s3:::$BUCKET_NAME/input/"] }], "ExcludeManagementEventSources": [] }]'

## Create an IAM role and apply the policy
aws iam create-role --role-name AWSCookbook407RuleRole --assume-role-policy-document file://policy1.json

## Attach the IAM Policy to the IAM Role
aws iam put-role-policy --role-name AWSCookbook407RuleRole --policy-name ECSRunTaskPermissionsForEvents --policy-document file://policy2.json

## Create an EventBridge Rule 
aws events put-rule --name "AWSCookbookRule" --role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/AWSCookbook407RuleRole" --event-pattern "{\"source\":[\"aws.s3\"],\"detail-type\":[\"AWS API Call\"],\"detail\":{\"eventSource\":[\"s3.amazonaws.com\"],\"eventName\":[\"CopyObject\",\"PutObject\",\"CompleteMultipartUpload\"],\"requestParameters\":{\"bucketName\":[\"$BUCKET_NAME\"]}}}"

## Create a rule target which specifies the ECS Cluster, Task Definition, Role, Networking parameters which specifies what CloudWatch Events will do when the rule is triggered
aws events put-targets --rule AWSCookbookRule --targets '{"Id":"AWSCookbookRuleID","Arn":"<<ECSClusterArn>>","RoleArn":"arn:aws:iam::$AWS_ACCOUNT_ID:role\/AWSCookbookRuleRole","EcsParameters":{"TaskDefinitionArn":"arn:aws:ecs:$AWS_REGION:$AWS_ACCOUNT_ID:task-definition\/awscookbook407","TaskCount":1,"LaunchType":"FARGATE","NetworkConfiguration":{"awsvpcConfiguration":{"Subnets":["<<VPCPrivateSubnets>>"],"SecurityGroups":["<<VPCDefaultSecurityGroup>>"],"AssignPublicIp":"ENABLED"}}}}'

## Create an IAM role using the task-execution-assume-role.json file
aws iam create-role --role-name AWSCookbook407ECS --assume-role-policy-document file://task-execution-assume-role.json

## Run the following commands to add IAM policies to the IAM Role
aws iam attach-role-policy --role-name AWSCookbook407ECS --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam attach-role-policy --role-name AWSCookbook407ECS --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

## Run Sed to setup taskdef.json
sed -e "s/AWS_ACCOUNT_ID/${AWS_ACCOUNT_ID}/g" -e "s/AWS_REGION/${AWS_REGION}/g" taskdef-template.json > taskdef.json

## Register the Task Definition 
aws ecs register-task-definition --execution-role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/AWSCookbook407ECS" --cli-input-json file://taskdef.json

## Clean Up 

## Destroy the Stack
cdk destroy 
