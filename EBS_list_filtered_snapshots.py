import argparse
import concurrent.futures
from datetime import datetime
from datetime import timezone

import boto3

"""
1. **Using the `--start_date` argument**:
   To filter snapshots starting from a specific date:
   python EBS_list_filtered_snapshots.py --start_date 2020-01-01
2. **Using the `--size` argument**:
   To filter snapshots by the size of their volumes (in GB):
   python EBS_list_filtered_snapshots.py --size 10
3. **Using the `--description` argument**:
   To search for a phrase within the description of snapshots:
   python EBS_list_filtered_snapshots.py --description "Backup for Project X"
4. **Combining multiple arguments**:
   You can combine multiple arguments to refine your search:
   python EBS_list_filtered_snapshots.py --start_date 2020-01-01 --size 10 --description "Backup for Project X"
"""


# Function to process a single snapshot
def process_snapshot(snapshot, start_date, size, description):
    creation_date = snapshot.start_time.replace(tzinfo=timezone.utc).astimezone(tz=None)

    # Filter by start date
    if start_date and creation_date.date() < start_date:
        return

    # Filter by size
    if size and snapshot.volume_size != size:
        return

    # Filter by description
    if description and description not in snapshot.description:
        return

    print(
        f"Snapshot ID: {snapshot.snapshot_id}, Started on: {snapshot.start_time}, Size: {snapshot.volume_size}GB, Description: {snapshot.description}"
    )


# Function to filter and print snapshots
def get_snapshots(start_date, size, description):
    ec2 = boto3.resource("ec2")

    print("Fetching all snapshots, please wait...")
    snapshots = list(ec2.snapshots.all())

    print(f"Processing {len(snapshots)} snapshots...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(
            process_snapshot,
            snapshots,
            [start_date] * len(snapshots),
            [size] * len(snapshots),
            [description] * len(snapshots),
        )


# Parse command line arguments
parser = argparse.ArgumentParser(description="Filter AWS EBS snapshots.")
parser.add_argument(
    "--start_date",
    type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
    help="The start date for the snapshots in the format YYYY-MM-DD.",
)
parser.add_argument("--size", type=int, help="The size of the volume in GB.")
parser.add_argument(
    "--description", type=str, help="A phrase to search for in the description."
)
args = parser.parse_args()

get_snapshots(args.start_date, args.size, args.description)
