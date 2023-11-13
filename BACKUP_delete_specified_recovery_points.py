import argparse
from datetime import datetime

import boto3

"""
1. **Basic Usage**: Just providing the vault name and the date.
   python script_name.py myVault "August 8, 2023"
2. **Verbose Mode**: If you want detailed information (i.e., `Resource Type`, `Backup Type`, and `Creation Date` in addition to the `Recovery Point ID`, `Resource Name`, and `Resource ID`).
   python script_name.py myVault "August 8, 2023" --verbose
3. **Max Deletion**: If you want the script to ask for confirmation every `n` deletions, let's say 5 deletions in this example.
   python script_name.py myVault "August 8, 2023" --max-deletion 5
4. **Verbose Mode and Max Deletion Combined**: For detailed information and confirmation every `n` deletions.
   python script_name.py myVault "August 8, 2023" --verbose --max-deletion 5
"""


def parse_date(date_str):
    """Converts date string into a datetime object."""
    return datetime.strptime(date_str, "%B %d, %Y")


def delete_old_recovery_points(vault_name, cutoff_date, max_deletion, verbose):
    client = boto3.client("backup")

    recovery_points_to_delete = []

    # Pagination for listing recovery points
    next_token = None
    while True:
        # Fetching recovery points from the specified vault
        if next_token:
            recovery_points = client.list_recovery_points_by_backup_vault(
                BackupVaultName=vault_name,
                ByCreatedBefore=cutoff_date,
                NextToken=next_token,
            )
        else:
            recovery_points = client.list_recovery_points_by_backup_vault(
                BackupVaultName=vault_name, ByCreatedBefore=cutoff_date
            )

        # Collecting relevant recovery points
        for point in recovery_points["RecoveryPoints"]:
            recovery_points_to_delete.append(point)

        # Handle pagination if there are more points to fetch
        if "NextToken" in recovery_points:
            next_token = recovery_points["NextToken"]
        else:
            break

    if not recovery_points_to_delete:
        print("No old recovery points found in the specified vault!")
        return

    print(
        f"\nFound {len(recovery_points_to_delete)} recovery points older than {cutoff_date} in vault {vault_name}."
    )

    # Prompting user to display the information of recovery points
    display_confirm = (
        input("Do you want to display the recovery point information? [y/N]: ")
        .strip()
        .lower()
    )
    if display_confirm == "y":
        for point in recovery_points_to_delete:
            print("\n" + "=" * 40)
            print(f"Recovery Point ID: {point['RecoveryPointArn'].split(':')[-1]}")
            print(f"Resource Name: {point.get('ResourceName', 'N/A')}")
            print(f"Resource ID: {point.get('ResourceId', 'N/A')}")
            if verbose:
                print(f"Resource Type: {point.get('ResourceType', 'N/A')}")
                print(f"Backup Type: {point.get('BackupType', 'N/A')}")
                print(f"Creation Date: {point['CreationDate'].date()}")
            print("=" * 40 + "\n")

    # Confirming with the user before deletion
    confirm = (
        input("Do you want to delete these recovery points? [y/N]: ").strip().lower()
    )
    if confirm != "y":
        print("Deletion cancelled.")
        return
    if max_deletion is None:
        confirm = (
            input(
                "Are you sure you want to delete all the listed recovery points? [y/N]: "
            )
            .strip()
            .lower()
        )
        if confirm != "y":
            print("Deletion cancelled.")
            return

    # Actual deletion process
    counter = 0
    for point in recovery_points_to_delete:
        counter += 1
        print(
            f"Deleting recovery point {point['RecoveryPointArn']} from vault {vault_name}..."
        )
        client.delete_recovery_point(
            BackupVaultName=vault_name, RecoveryPointArn=point["RecoveryPointArn"]
        )

        # Prompting user again after `max_deletion` number of deletions
        if max_deletion and counter % max_deletion == 0:
            confirm = (
                input(f"{max_deletion} recovery points deleted. Continue? [y/N]: ")
                .strip()
                .lower()
            )
            if confirm != "y":
                print("Deletion process halted.")
                return

    print("Deletion completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete AWS Backup recovery points older than a given date from a specified vault."
    )
    parser.add_argument("vault", help="Name of the backup vault.")
    parser.add_argument(
        "date",
        type=parse_date,
        help='The cutoff date in the format "Month Day, Year". E.g., "August 8, 2023"',
    )
    parser.add_argument(
        "--max-deletion",
        type=int,
        help="Maximum number of deletions before user confirmation is required again.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Provide verbose output."
    )
    args = parser.parse_args()

    delete_old_recovery_points(args.vault, args.date, args.max_deletion, args.verbose)
