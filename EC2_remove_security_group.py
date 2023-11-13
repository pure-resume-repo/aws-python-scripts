import argparse

import boto3


def remove_security_group_from_instance(instance_id, security_group_id):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)

    # Get the current security group IDs attached to the instance
    current_security_group_ids = [sg["GroupId"] for sg in instance.security_groups]

    # Remove the specified security group ID from the list
    if security_group_id in current_security_group_ids:
        current_security_group_ids.remove(security_group_id)

    # Update the instance with the new list of security group IDs
    instance.modify_attribute(Groups=current_security_group_ids)


def main():
    parser = argparse.ArgumentParser(
        description="Remove a security group from a list of existing EC2 instances"
    )
    parser.add_argument(
        "instances_file", help="A text file containing one instance ID per line"
    )
    parser.add_argument(
        "security_group_id", help="The ID of the security group to remove"
    )
    args = parser.parse_args()

    # Read the list of instance IDs from the text file
    with open(args.instances_file) as f:
        instance_ids = [line.strip() for line in f.readlines()]

    # Remove the security group from each instance
    for instance_id in instance_ids:
        remove_security_group_from_instance(instance_id, args.security_group_id)


if __name__ == "__main__":
    main()
