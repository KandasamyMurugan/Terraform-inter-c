import boto3

ec2 = boto3.client('ec2')
backup = boto3.client('backup')

BACKUP_PLAN_ID = 'awsbackup-automation-for-running-instances'

def lambda_handler(event, context):
    # Get list of running instances
    running_instances = []
    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            running_instances.append(instance['InstanceId'])

    # Get list of instances already in AWS Backup
    protected_resources = backup.list_protected_resources()
    protected_instances = {res['ResourceArn'].split('/')[-1] for res in protected_resources['Results']}

    # Add missing instances to AWS Backup
    for instance_id in running_instances:
        if instance_id not in protected_instances:
            backup.tag_resource(ResourceArn=f'arn:aws:ec2:{region}:{account-id}:instance/{instance_id}',
                                Tags={'Backup': 'Enabled'})
            print(f'Added {instance_id} to AWS Backup')

    return {"message": "Backup sync completed"}
