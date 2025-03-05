import boto3

ec2 = boto3.client('ec2')
backup = boto3.client('backup')

BACKUP_PLAN_ID = '722cf2d2-070b-4431-9761-c0150f074225'

def lambda_handler(event, context):
    # Get list of running instances
    running_instances = []
    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            running_instances.append(instance['InstanceId'])

    # Get existing backup selections
    existing_selections = backup.list_backup_selections(BackupPlanId=BACKUP_PLAN_ID)
    existing_resources = set()

    for selection in existing_selections['BackupSelectionsList']:
        selection_details = backup.get_backup_selection(
            BackupPlanId=BACKUP_PLAN_ID,
            SelectionId=selection['SelectionId']
        )
        existing_resources.update(selection_details['BackupSelection']['Resources'])

    # Add missing instances to AWS Backup Plan
    for instance_id in running_instances:
        instance_arn = f'arn:aws:ec2:us-east-1:205930609030:instance/{instance_id}'
        if instance_arn not in existing_resources:
            backup.create_backup_selection(
                BackupPlanId=BACKUP_PLAN_ID,
                BackupSelection={
                    'SelectionName': f'Backup-{instance_id}',
                    'IamRoleArn': 'arn:aws:iam::205930609030:role/service-role/AWSBackupDefaultServiceRole',
                    'Resources': [instance_arn]
                }
            )
            print(f'Added {instance_id} to AWS Backup Plan')

            return {"message": "Backup sync completed"}
