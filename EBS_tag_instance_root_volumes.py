import argparse

import boto3

# this scripts takes a file with instance ids and and a file with tags and applies those tags to the root volume of those instances
# usagage: python script.py --instances instances.txt --tags tags.txt


def read_file(filename):
    with open(filename) as file:
        return [line.strip() for line in file]


def main():
    # Parse the arguments
    parser = argparse.ArgumentParser(
        description="Add tags to EC2 instances and their root volumes"
    )
    parser.add_argument(
        "--instances",
        required=True,
        help="File containing EC2 instance IDs, one per line",
    )
    parser.add_argument(
        "--tags",
        required=True,
        help="File containing tags in the format Key=Value, one per line",
    )
    args = parser.parse_args()

    # Read instance IDs and tags from the files
    instance_ids = read_file(args.instances)
    raw_tags = read_file(args.tags)
    tags = [{"Key": tag.split("=")[0], "Value": tag.split("=")[1]} for tag in raw_tags]

    # Initialize the EC2 client
    ec2 = boto3.client("ec2")

    # Collect root volumes
    root_volumes = []

    # Loop through the instance IDs
    for instance_id in instance_ids:
        # Describe the instance to get attached volume IDs and Tags
        try:
            response = ec2.describe_instances(InstanceIds=[instance_id])
        except Exception as e:
            print(f"Error processing Instance ID {instance_id}: {e}")
            continue

        instance = response["Reservations"][0]["Instances"][0]
        block_device_mappings = instance["BlockDeviceMappings"]

        # Extract the instance name from the tags
        instance_name = None
        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                instance_name = tag["Value"]
                break

        print(f"Processing Instance ID: {instance_id}, Instance Name: {instance_name}")

        # Loop through the block device mappings
        for block_device_mapping in block_device_mappings:
            # Check if it is the root volume (device name usually is '/dev/sda1' or '/dev/xvda')
            if block_device_mapping["DeviceName"] in ["/dev/sda1", "/dev/xvda"]:
                root_volume_id = block_device_mapping["Ebs"]["VolumeId"]
                root_volumes.append((instance_id, instance_name, root_volume_id))

    # Print the volumes to be tagged
    print("The following root volumes will be tagged:")
    for instance_id, instance_name, volume_id in root_volumes:
        print(f"Instance ID: {instance_id}, Instance Name: {instance_name}")
        print(f"  Root Volume ID: {volume_id}")

    # Ask user for confirmation
    user_input = input("Are you ready to tag the volumes? (yes/no): ")
    if user_input.lower() != "yes":
        print("Tagging cancelled.")
        return

    # Tag the volumes
    for instance_id, instance_name, volume_id in root_volumes:
        ec2.create_tags(Resources=[volume_id], Tags=tags)

    # Print confirmation
    print("\nThe following volumes have been tagged:")
    for instance_id, instance_name, volume_id in root_volumes:
        print(f"Instance ID: {instance_id}, Instance Name: {instance_name}")
        print(f"  Root Volume ID: {volume_id}")

        # Get and print the tags for each volume
        volume_info = ec2.describe_volumes(VolumeIds=[volume_id])
        volume_tags = volume_info["Volumes"][0]["Tags"]
        print(f"  Tags for volume {volume_id}:")
        for tag in volume_tags:
            print(f"    Key: {tag['Key']}, Value: {tag['Value']}")
        print("\n")


if __name__ == "__main__":
    main()
