import argparse
import json
import time

import boto3


def get_snapshot_info(snapshot_ids):
    ec2_client = boto3.client("ec2")
    cloudtrail_client = boto3.client("cloudtrail")

    for snapshot_id in snapshot_ids:
        response = ec2_client.describe_snapshots(SnapshotIds=[snapshot_id])

        for snapshot in response["Snapshots"]:
            print(f"Snapshot ID: {snapshot['SnapshotId']}")
            print(f"Started on: {snapshot['StartTime']}")
            print(f"Description: {snapshot['Description']}")

            # Find the creator from CloudTrail logs
            paginator = cloudtrail_client.get_paginator("lookup_events")

            for page in paginator.paginate(
                LookupAttributes=[
                    {
                        "AttributeKey": "ResourceName",
                        "AttributeValue": snapshot["SnapshotId"],
                    },
                ]
            ):
                for event in page["Events"]:
                    event_dict = json.loads(event["CloudTrailEvent"])
                    if event_dict.get("eventName") == "CreateSnapshot":
                        print(f"Created by: {event_dict['userIdentity']['arn']}")

            print()
            time.sleep(0.5)  # sleep for 500 milliseconds


# Parse command line arguments
parser = argparse.ArgumentParser(description="Process snapshot file.")
parser.add_argument("filename", help="The name of the file containing snapshot IDs.")
args = parser.parse_args()

# Read snapshot IDs from a file
with open(args.filename) as file:
    snapshot_ids = [line.strip() for line in file]

get_snapshot_info(snapshot_ids)
