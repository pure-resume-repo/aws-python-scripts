import argparse

import boto3


def add_security_group_to_instance(instance_id, new_security_group_id):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)

    # Get the current security group IDs attached to the instance
    current_security_group_ids = [sg["GroupId"] for sg in instance.security_groups]

    # Add the new security group ID to the list
    current_security_group_ids.append(new_security_group_id)

    # Update the instance with the new list of security group IDs
    instance.modify_attribute(Groups=current_security_group_ids)


def main():
    parser = argparse.ArgumentParser(
        description="Add a security group to a list of existing EC2 instances"
    )
    parser.add_argument(
        "instances_file", help="A text file containing one instance ID per line"
    )
    parser.add_argument(
        "new_security_group_id", help="The ID of the new security group to add"
    )
    args = parser.parse_args()

    # Read the list of instance IDs from the text file
    with open(args.instances_file) as f:
        instance_ids = [line.strip() for line in f.readlines()]

    # Add the security group to each instance
    for instance_id in instance_ids:
        add_security_group_to_instance(instance_id, args.new_security_group_id)


if __name__ == "__main__":
    main()
