import argparse

import boto3


def read_instance_ids_from_file(file_name):
    with open(file_name) as file:
        instance_ids = [line.strip() for line in file]
    return instance_ids


def get_instance_name(tags):
    for tag in tags:
        if tag["Key"] == "Name":
            return tag["Value"]
    return "Unknown"  # Return Unknown if no Name tag found


def get_instance_details(instance_ids):
    ec2 = boto3.resource("ec2")

    for instance_id in instance_ids:
        instance = ec2.Instance(instance_id)
        print(f"Instance Name: {get_instance_name(instance.tags)}")
        print(f"ID: {instance.instance_id}")
        print(f"VPC: {instance.vpc_id}")
        print(f"Private IP: {instance.private_ip_address}")
        print(f"Public IP: {instance.public_ip_address}")
        print(f"Tags: {instance.tags}")
        print(f"Key Name: {instance.key_name}")
        print(
            f"Security Groups: {', '.join([sg['GroupName'] for sg in instance.security_groups])}"
        )

        try:
            print(f"OS: {instance.platform}")
        except Exception:
            print("OS: Unknown")

        print("\n-----------------------------\n")


def main(file_name):
    instance_ids = read_instance_ids_from_file(file_name)
    get_instance_details(instance_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get AWS instance details.")
    parser.add_argument("file", help="File name containing the list of instance IDs.")
    args = parser.parse_args()

    main(args.file)
