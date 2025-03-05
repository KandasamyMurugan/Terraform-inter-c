# Create AWS backup plan

aws backup create-backup-plan \
           --backup-plan '{"BackupPlanName": "EC2-AutoBackup","Rules":[{"RuleName":"DailyBackup","TargetBackupVaultName":"Default","ScheduleExpression":"cron(0 0 * * ? *)"}]}'

#Create a Lambda Function for Auto Backup
import boto3

ec2 = boto3.client('ec2')
backup = boto3.client('backup')

BACKUP_PLAN_ID = "b29d45e4-11cf-40c4-854a-0108401850a0"  # Replace with actual Backup Plan ID

def lambda_handler(event, context):
    # Get list of running instances
    running_instances = []
    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            running_instances.append(instance['InstanceId'])

    # Get instances already in AWS Backup
    protected_resources = backup.list_protected_resources()
    protected_instances = {res['ResourceArn'].split('/')[-1] for res in protected_resources['Results']}

    # Add missing instances to AWS Backup
    for instance_id in running_instances:
        if instance_id not in protected_instances:
            backup.create_backup_selection(
                BackupPlanId=BACKUP_PLAN_ID,
                BackupSelection={
                    "SelectionName": "EC2AutoBackup",
                    "IamRoleArn": "arn:aws:iam::205930609030:role/service-role/AWSBackupDefaultServiceRole",
                    "Resources": [f"arn:aws:ec2:us-east-1:205930609030:instance/{instance_id}"]
                }
            )
            print(f"Added {instance_id} to AWS Backup")

    return {"message": "Backup sync completed"}
--------------------------------------------------------------

aws events put-targets \
           --rule lambda-backup-cron-job \
                            --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:205930609030:function:aws-backup"
===========================================================================

aws lambda add-permission \
    --function-name aws-backup\
    --statement-id AllowEventBridgeInvokeEvery20Mins \
    --action "lambda:InvokeFunction" \
    --principal "events.amazonaws.com" \
    --source-arn "arn:aws:events:us-east-1:205930609030:rule/lambda-backup-cron-job"
=============================================================


aws backup create-backup-selection \
    --backup-plan-id b29d45e4-11cf-40c4-854a-0108401850a0 \
    --selection-name "TestBackupSelection" \
    --resources-arn "arn:aws:ec2:us-east-1:205930609030:instance/YOUR_INSTANCE_ID"



aws backup start-backup-job \
    --backup-vault-name "Default" \
    --resource-arn "arn:aws:ec2:us-east-1:205930609030:instance/i-0682cc793770271b1" \
    --iam-role-arn "arn:aws:iam::205930609030:role/service-role/AWSBackupDefaultServiceRole"


aws backup start-backup-job \
    --backup-vault-name Default \
    --resource-arn arn:aws:ec2:us-east-1:205930609030:instance/i-00c34c48a1936da9f \
--iam-role-arn arn:aws:iam::205930609030:role/service-role/AWSBackupDefaultServiceRole





import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    for record in event['Records']:
        detail = record['detail']
        if detail['state'] == 'running':
            instance_id = detail['instance-id']
            ec2.create_tags(
                Resources=[instance_id],
                Tags=[{'Key': 'Backup', 'Value': 'Yes'}]
            )
            print(f"Tagged instance {instance_id} with Backup=Yes")


{
    "source": ["aws.ec2"],
    "detail-type": ["EC2 Instance State-change Notification"],
    "detail": { "state": ["running"] }
}

import boto3

ec2 = boto3.client('ec2')
backup = boto3.client('backup')

def lambda_handler(event, context):
    # Get all backup selections
    backup_vault = "Ec2-backup-1hour"  # Replace with your vault name
    response = backup.list_protected_resources()

    for resource in response['Results']:
        if resource['ResourceType'] == 'EC2':
            instance_id = resource['ResourceArn'].split('/')[-1]

            # Check if the instance exists
            try:
                ec2.describe_instances(InstanceIds=[instance_id])
            except ec2.exceptions.ClientError as e:
                if 'InvalidInstanceID.NotFound' in str(e):
                    # Remove instance from AWS Backup
                    backup.delete_protected_resource(ResourceArn=resource['ResourceArn'])
                    print(f"Removed terminated instance {instance_id} from backup")

