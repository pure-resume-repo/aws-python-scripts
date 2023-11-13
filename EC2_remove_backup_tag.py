import boto3

ec2 = boto3.client("ec2")

# List of instances and their corresponding IDs
instances = {}

# Tag value to set
tag = {"Key": "StandardBackup", "Value": "False"}

# Iterate over instances
for instance_name, instance_id in instances.items():
    # Add or modify tag
    print(f"Modifying tag for instance: {instance_name} ({instance_id})")
    ec2.create_tags(Resources=[instance_id], Tags=[tag])
