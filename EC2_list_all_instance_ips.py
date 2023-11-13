import boto3

# Create an EC2 resource object using the AWS SDK for Python (boto3)
ec2 = boto3.resource("ec2")

# Create an EC2 client
client = boto3.client("ec2")

# Use the filter() method of the instances collection to retrieve all running EC2 instances
instances = ec2.instances.all()

# Print the instance details
for instance in instances:
    # Fetch instance tags
    tags = client.describe_tags(
        Filters=[
            {
                "Name": "resource-id",
                "Values": [
                    instance.id,
                ],
            }
        ]
    )

    # Get the name tag which is the instance name
    name_tags = [tag["Value"] for tag in tags["Tags"] if tag["Key"] == "Name"]

    # Check if name tag is present, else default to 'No Name'
    name = name_tags[0] if name_tags else "No Name"

    # Get the instance state
    state = instance.state["Name"]

    # Print the name, instance ID, private IP, public IP, and state separated by commas
    print(
        f"{name},{instance.id},{instance.private_ip_address},{instance.public_ip_address},{state}"
    )
