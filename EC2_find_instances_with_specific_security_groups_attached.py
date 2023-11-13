import argparse

import boto3


def load_sg_ids_from_file(filename):
    with open(filename) as file:
        return [line.strip() for line in file]


def check_sg_usage(sg_ids):
    ec2 = boto3.resource("ec2")

    # Check EC2 instances
    instances = ec2.instances.all()
    for instance in instances:
        for sg in instance.security_groups:
            if sg["GroupId"] in sg_ids:
                print(
                    f"Security Group {sg['GroupId']} is being used by EC2 instance: {instance.id}"
                )

    # Check RDS instances
    rds = boto3.client("rds")
    rds_instances = rds.describe_db_instances()
    for instance in rds_instances["DBInstances"]:
        for sg in instance["VpcSecurityGroups"]:
            if sg["VpcSecurityGroupId"] in sg_ids:
                print(
                    f"Security Group {sg['VpcSecurityGroupId']} is being used by RDS instance: {instance['DBInstanceIdentifier']}"
                )


if __name__ == "__main__":
    # Argument parser for optional security groups file
    parser = argparse.ArgumentParser(
        description="Check usage of security groups in EC2 and RDS instances"
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help="File containing security group IDs, one per line",
    )
    args = parser.parse_args()

    # Load security group IDs from file
    sg_ids = load_sg_ids_from_file(args.file)

    # Check usage of security groups
    check_sg_usage(sg_ids)
