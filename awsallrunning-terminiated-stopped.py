import boto3
import os

# AWS Clients
ec2 = boto3.client('ec2')
backup = boto3.client('backup')

# Set environment variables in Lambda for these values
BACKUP_PLAN_ID = os.environ['722cf2d2-070b-4431-9761-c0150f074225']
BACKUP_VAULT_NAME = os.environ['Default']
IAM_ROLE_ARN = os.environ['arn:aws:iam::205930609030:role/service-role/AWSBackupDefaultServiceRole']

def get_running_instances():
    """Fetches running EC2 instances and returns their ARNs."""
    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    instances = [
        f"arn:aws:ec2:{os.environ['us-east-1']}:{os.environ['205930609030']}:instance/{instance['InstanceId']}"
        for reservation in response['Reservations']
        for instance in reservation['Instances']
    ]
    return instances

def delete_old_backup_selection():
    """Deletes the existing backup selection."""
    try:
        selections = backup.list_backup_selections(BackupPlanId=BACKUP_PLAN_ID)
        for selection in selections.get('BackupSelectionsList', []):
            backup.delete_backup_selection(
                BackupPlanId=BACKUP_PLAN_ID,
                SelectionId=selection['SelectionId']
            )
        print("Old backup selections deleted.")
    except Exception as e:
        print(f"Error deleting backup selection: {e}")

def create_new_backup_selection(instance_arns):
    """Creates a new backup selection with running instances."""
    if not instance_arns:
        print("No running instances found.")
        return

    try:
        response = backup.create_backup_selection(
            BackupPlanId=BACKUP_PLAN_ID,
            BackupSelection={
                "SelectionName": "UpdatedBackupSelection",
                "IamRoleArn": IAM_ROLE_ARN,
                "Resources": instance_arns
            }
        )
        print("New backup selection created:", response)
    except Exception as e:
        print(f"Error creating backup selection: {e}")

def start_manual_backup(instance_arn):
    """Manually starts a backup job for a given instance."""
    try:
        response = backup.start_backup_job(
            BackupVaultName=BACKUP_VAULT_NAME,
            ResourceArn=instance_arn,
            IamRoleArn=IAM_ROLE_ARN,
            StartWindowMinutes=60,
            CompleteWindowMinutes=1440,  # 24 hours
            Lifecycle={"DeleteAfterDays": 30}
        )
        print(f"Backup started for {instance_arn}: {response['BackupJobId']}")
    except Exception as e:
        print(f"Error starting backup: {e}")

def lambda_handler(event, context):
    """Main Lambda function entry point."""
    print("Fetching running EC2 instances...")
    running_instances = get_running_instances()

    print("Updating AWS Backup selections...")
    delete_old_backup_selection()
    create_new_backup_selection(running_instances)

    if running_instances:
        print("Starting manual backups...")
        for instance in running_instances:
            start_manual_backup(instance)

    return {"statusCode": 200, "message": "Backup update and manual job triggered."}
