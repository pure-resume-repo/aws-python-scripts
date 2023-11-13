import argparse

import boto3

# Define argument parser
parser = argparse.ArgumentParser(description="Delete specific AWS EBS volumes.")
parser.add_argument("file", help="Text file with volume IDs, one per line.")

# Parse arguments
args = parser.parse_args()

# Create a session using your AWS credentials
session = boto3.Session()

# Create an EC2 resource object using the defined session
ec2_resource = session.resource("ec2")

# Read the volume IDs from the text file
with open(args.file) as file:
    volume_ids = [line.strip() for line in file]

# Iterate over each volume ID
for volume_id in volume_ids:
    # Load volume information
    volume = ec2_resource.Volume(volume_id)

    # Check if the volume is available, not encrypted and has 'remediated' tag
    if volume.state == "available" and not volume.encrypted:
        if volume.tags:
            for tag in volume.tags:
                if tag["Key"] == "remediated":
                    # Delete the volume
                    volume.delete()
                    print(f"Deleted volume: {volume_id}")
                    break
