import argparse

import boto3

# Create an EC2 resource object using the AWS SDK
ec2_resource = boto3.resource("ec2")


def delete_snapshots_from_file(file_path):
    # Read snapshot IDs from the provided file
    with open(file_path) as file:
        snapshot_ids = file.read().splitlines()

    initial_confirm = input(
        f"WARNING: You are about to delete {len(snapshot_ids)} snapshots. This action cannot be undone. Do you want to proceed? (y/n): "
    )
    if initial_confirm.lower() != "y":
        print("Exiting without deleting any snapshots.")
        return

    for i, snapshot_id in enumerate(snapshot_ids, start=1):
        try:
            # Every 10 snapshots, ask for confirmation
            if i % 10 == 0:
                confirm = input(
                    f"You're about to delete the 10th snapshot ({snapshot_id}), do you want to continue? (y/n): "
                )
                if confirm.lower() != "y":
                    print("Exiting without deleting the snapshot.")
                    return
            snapshot = ec2_resource.Snapshot(snapshot_id)
            snapshot.delete()
            print(f"Deleted snapshot: {snapshot_id}")
        except Exception as e:
            print(f"Error deleting snapshot: {snapshot_id}. Error: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_path", help="Path to the file containing the list of Snapshot IDs"
    )
    args = parser.parse_args()

    delete_snapshots_from_file(args.file_path)
