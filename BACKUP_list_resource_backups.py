import boto3

# List of instance IDs
instance_ids = []

# AWS region
region = "us-west-2"

# Initialize the Boto3 client for AWS Backup
backup_client = boto3.client("backup", region_name=region)

# Iterate through each instance ID
for instance_id in instance_ids:
    # Construct the resource ARN
    resource_arn = f"arn:aws:ec2:{region}:123456666:instance/{instance_id}"

    # List recovery points for the current resource
    try:
        response = backup_client.list_recovery_points_by_resource(
            ResourceArn=resource_arn
        )
        print(f"Recovery points for instance {instance_id}:")
        for recovery_point in response["RecoveryPoints"]:
            print(f"- Recovery Point ARN: {recovery_point['RecoveryPointArn']}")
    except Exception as e:
        print(f"Error listing recovery points for instance {instance_id}: {e}")
