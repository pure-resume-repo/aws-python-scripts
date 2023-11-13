#!/usr/bin/env python3
from collections import defaultdict

import boto3


def get_asg_instances(client):
    paginator = client.get_paginator("describe_auto_scaling_groups")
    for page in paginator.paginate():
        for group in page["AutoScalingGroups"]:
            for instance in group["Instances"]:
                yield group["AutoScalingGroupName"], instance["InstanceId"]


def get_instance_volumes_and_name(ec2, instance_id):
    instance = ec2.Instance(instance_id)
    volumes = list(instance.volumes.all())
    name_tag = next(
        (tag["Value"] for tag in instance.tags or [] if tag["Key"] == "Name"), None
    )
    return volumes, name_tag


def main():
    client = boto3.client("autoscaling")
    ec2 = boto3.resource("ec2")

    instances_to_terminate = defaultdict(list)

    # Find instances in auto scaling groups
    for group_name, instance_id in get_asg_instances(client):
        volumes, name = get_instance_volumes_and_name(ec2, instance_id)

        # Check if any volume is not encrypted
        if any(not volume.encrypted for volume in volumes):
            instances_to_terminate[group_name].append((instance_id, name))

    # List instances to be terminated
    if not instances_to_terminate:
        print("No instances with unencrypted volumes found in auto scaling groups.")
        return

    print("Instances with unencrypted volumes:")
    for group_name, instances in instances_to_terminate.items():
        print(f"\nAuto Scaling Group: {group_name}")
        for instance_id, name in instances:
            print(f" - Instance ID: {instance_id}, Name: {name}")

    # Confirm termination
    confirmation = input("\nDo you want to terminate these instances? (yes/no): ")
    if confirmation.lower() == "yes":
        for instances in instances_to_terminate.values():
            for instance_id, _ in instances:
                ec2.Instance(instance_id).terminate()
                print(f"Terminated instance {instance_id}")


if __name__ == "__main__":
    main()
