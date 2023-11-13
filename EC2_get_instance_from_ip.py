import argparse

import boto3


def find_ec2_instances(csv_file_path):
    # Read IP addresses from the CSV file
    with open(csv_file_path) as file:
        ip_addresses = file.read().strip().split(",")

    # Create a Boto3 session
    session = boto3.Session()
    ec2 = session.resource("ec2")

    # Retrieve EC2 instances
    instances = ec2.instances.filter(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    # Find instances with the given IP addresses and print their details
    for instance in instances:
        for interface in instance.network_interfaces:
            if interface.private_ip_address in ip_addresses:
                print(f"Instance ID: {instance.id}")
                print(f"Subnet: {interface.subnet_id}")
                print(f"VPC: {instance.vpc_id}")

                # Get the instance name from the Name tag
                instance_name = None
                for tag in instance.tags:
                    if tag["Key"] == "Name":
                        instance_name = tag["Value"]
                        break
                print(f"Instance Name: {instance_name}")

                # Print security groups
                security_groups = [sg["GroupName"] for sg in instance.security_groups]
                print(f"Security Groups: {', '.join(security_groups)}")
                print("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find EC2 instances based on a CSV file of IP addresses"
    )
    parser.add_argument(
        "csv_file", help="Path to the CSV file containing the IP addresses"
    )
    args = parser.parse_args()

    find_ec2_instances(args.csv_file)
