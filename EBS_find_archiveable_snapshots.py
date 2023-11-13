import argparse

import boto3

# Initialize a session using your credentials
session = boto3.Session()

# Initialize the EC2 client
ec2 = session.client("ec2")


# Function to check if snapshot is associated with an AMI
def is_snapshot_associated_with_ami(snapshot_id):
    images = ec2.describe_images(
        Owners=["self"],
        Filters=[{"Name": "block-device-mapping.snapshot-id", "Values": [snapshot_id]}],
    )
    return len(images["Images"]) > 0


def main(verbose, archivable_only):
    # Retrieve the list of snapshots
    snapshots = ec2.describe_snapshots(OwnerIds=["self"])

    # Counters
    archivable_count = 0
    aws_backup_count = 0
    ami_count = 0
    not_completed_count = 0
    root_device_ami_count = 0

    # List to store eligible snapshots for archiving
    archivable_snapshots = []

    # Iterate through each snapshot
    for snapshot in snapshots["Snapshots"]:
        snapshot_id = snapshot["SnapshotId"]

        # Rule 1: Check if the snapshot is in the 'completed' state
        if snapshot["State"] != "completed":
            if verbose and not archivable_only:
                print(f"Snapshot {snapshot_id} is not in the 'completed' state.")
            not_completed_count += 1

        # Rule 2: Skip snapshots of root device volume of registered AMI
        if snapshot.get("Description", "").startswith("Created by CreateImage"):
            if verbose and not archivable_only:
                print(
                    f"Snapshot {snapshot_id} is of the root device volume of a registered AMI."
                )
            root_device_ami_count += 1

        # Rule 3: Check if snapshot is associated with an AMI
        if is_snapshot_associated_with_ami(snapshot_id):
            if verbose and not archivable_only:
                print(f"Snapshot {snapshot_id} is associated with an EBS-backed AMI.")
            ami_count += 1

        # Rule 4: Check if snapshot is created by AWS Backup
        if any(
            tag.get("Key").startswith("aws:backup:") for tag in snapshot.get("Tags", [])
        ):
            if verbose and not archivable_only:
                print(f"Snapshot {snapshot_id} was created by AWS Backup.")
            aws_backup_count += 1

        # Update counts based on whether the snapshot is archivable or not
        if (
            snapshot["State"] == "completed"
            and not snapshot.get("Description", "").startswith("Created by CreateImage")
            and not is_snapshot_associated_with_ami(snapshot_id)
            and not any(
                tag.get("Key").startswith("aws:backup:")
                for tag in snapshot.get("Tags", [])
            )
        ):
            archivable_count += 1
            archivable_snapshots.append(snapshot_id)

    # Print the results
    if archivable_only:
        print("Snapshots eligible for archiving:")
        for snap_id in archivable_snapshots:
            print(snap_id)
    else:
        print(f"Total snapshots in the account: {len(snapshots['Snapshots'])}")
        print(f"Snapshots available to be archived: {archivable_count}")
        print(f"Snapshots not in 'completed' state: {not_completed_count}")
        print(
            f"Snapshots of root device volume of registered AMI: {root_device_ami_count}"
        )
        print(f"Snapshots that are part of AWS backups: {aws_backup_count}")
        print(f"Snapshots that are part of an AMI: {ami_count}")


if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(
        description="Find AWS snapshots eligible for archiving."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed information for each snapshot",
    )
    parser.add_argument(
        "--archivable-only",
        action="store_true",
        help="Print only the IDs of snapshots eligible for archiving",
    )
    args = parser.parse_args()

    # Execute the main function with the verbose and archivable_only flags
    main(args.verbose, args.archivable_only)
