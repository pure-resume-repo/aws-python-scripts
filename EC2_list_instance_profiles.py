import argparse
import csv
from collections import defaultdict

import boto3
from termcolor import colored

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("--profile", help="Instance profile ARN")
parser.add_argument("--csv", help="CSV output file")
args = parser.parse_args()

# Create the session
session = boto3.Session()

# Create EC2 resource object
ec2_resource = session.resource("ec2")

# List all instances
instances = ec2_resource.instances.all()

# Dictionary to hold instances by profile name
instances_by_profile = defaultdict(list)
# Dictionary to hold counts of instances by profile name
profile_counts = defaultdict(int)

# For each instance
for instance in instances:
    profile_arn = None
    # If the instance has an instance profile
    if instance.iam_instance_profile:
        profile_arn = instance.iam_instance_profile["Arn"]

    # If the profile ARN is set and the user either did not provide an argument or the argument matches the profile ARN
    if profile_arn and (not args.profile or args.profile == profile_arn):
        instances_by_profile[profile_arn].append(instance)
        profile_counts[profile_arn] += 1

# Output to CSV
if args.csv:
    with open(args.csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Profile ARN", "Instance ID"])

        for profile_arn, instances in instances_by_profile.items():
            for instance in instances:
                writer.writerow([profile_arn, instance.id])

# Output to console
else:
    for profile_arn, instances in instances_by_profile.items():
        print(colored(f"Profile ARN: {profile_arn}", "yellow"))
        print("Instance IDs:")
        for instance in instances:
            print(" -", instance.id)
        print("\n")

    print(colored("Instance Counts:", "blue"))
    print("Profile ARN\tCount")
    for arn, count in profile_counts.items():
        print(f"{arn}\t{count}")
