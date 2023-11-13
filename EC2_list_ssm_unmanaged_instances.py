import argparse

import boto3


def get_all_ec2_instances():
    ec2 = boto3.resource("ec2")
    return list(ec2.instances.all())


def get_managed_instances():
    ssm = boto3.client("ssm")
    managed_instances = []
    paginator = ssm.get_paginator("describe_instance_information")

    for page in paginator.paginate():
        for instance_info in page["InstanceInformationList"]:
            managed_instances.append(instance_info["InstanceId"])
    return managed_instances


def compare_instances(inverse=False):
    all_instances = [
        instance
        for instance in get_all_ec2_instances()
        if instance.state["Name"] == "running"
    ]
    managed_instances = get_managed_instances()

    if inverse:
        return [
            instance for instance in all_instances if instance.id in managed_instances
        ]
    else:
        return [
            instance
            for instance in all_instances
            if instance.id not in managed_instances
        ]


def print_instance_details(instance, verbose=False):
    name_tag = next(
        (tag["Value"] for tag in instance.tags or [] if tag["Key"] == "Name"),
        instance.id,
    )
    if verbose:
        print(
            f"Instance ID: {instance.id}, Name: {name_tag}, State: {instance.state['Name']}, Type: {instance.instance_type}, Launch Time: {instance.launch_time}"
        )
    else:
        print(
            f"Instance ID: {instance.id}, Name: {name_tag}, State: {instance.state['Name']}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find instances not managed by Systems Manager Fleet Manager."
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Provide verbose output."
    )
    parser.add_argument(
        "--inverse",
        action="store_true",
        help="List instances that are managed by Fleet Manager.",
    )
    args = parser.parse_args()

    instances = compare_instances(inverse=args.inverse)

    if args.inverse:
        print("EC2 instances managed by Systems Manager Fleet Manager:")
    else:
        print("EC2 instances not managed by Systems Manager Fleet Manager:")

    for instance in instances:
        print_instance_details(instance, verbose=args.verbose)
