import argparse

import boto3

# Create an EC2 resource object
ec2_resource = boto3.resource("ec2")


# Define a function to get all running instances
def get_running_instances():
    running_instances = ec2_resource.instances.filter(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )
    return running_instances


# Define a function to get all security groups for a running instance
def get_security_groups(instance, sg_ids=None):
    security_groups = []
    for sg in instance.security_groups:
        if sg_ids is None or sg["GroupId"] in sg_ids:
            security_groups.append((sg["GroupId"], sg["GroupName"]))
    return security_groups


# Function to load security group IDs from file
def load_sg_ids_from_file(filename):
    with open(filename) as file:
        return [line.strip() for line in file]


if __name__ == "__main__":
    # Argument parser for optional security groups file
    parser = argparse.ArgumentParser(
        description="List security groups associated with running EC2 instances"
    )
    parser.add_argument(
        "-f", "--file", help="File containing security group IDs, one per line"
    )
    parser.add_argument(
        "--ids-only", action="store_true", help="Print only security group IDs"
    )
    args = parser.parse_args()

    # Load security group IDs from file if specified
    sg_ids = load_sg_ids_from_file(args.file) if args.file else None

    # Get all running instances
    running_instances = get_running_instances()

    # List of security groups
    security_groups_list = []

    # Get the security groups for each running instance
    for instance in running_instances:
        security_groups = get_security_groups(instance, sg_ids)
        security_groups_list.extend(security_groups)

    # Remove duplicates
    unique_security_groups = set(security_groups_list)

    # Print the unique security groups
    for sg_id, sg_name in unique_security_groups:
        if args.ids_only:
            print(sg_id)
        else:
            print("-------------------------------")
            print(f"Security Group: {sg_name}")
            print(f"{sg_id}")
    print("-------------------------------")
