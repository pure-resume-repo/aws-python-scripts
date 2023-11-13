import argparse
from operator import itemgetter

import boto3


def main(min_volume_size, filter_backup, csv_format):
    ec2_client = boto3.client("ec2")

    # Get all instances
    reservations = ec2_client.describe_instances()["Reservations"]

    # Gather instances with volumes
    instances = []

    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            standard_backup = None

            # Get tags
            for tag in instance.get("Tags", []):
                if tag["Key"] == "StandardBackup":
                    standard_backup = tag["Value"]

            # If filter_backup is set, skip instances that don't match the criteria
            if filter_backup is not None and standard_backup != filter_backup:
                continue

            # Get attached volumes
            volume_ids = [v["Ebs"]["VolumeId"] for v in instance["BlockDeviceMappings"]]
            volumes = []

            # Get volume sizes
            for volume_id in volume_ids:
                volume_info = ec2_client.describe_volumes(VolumeIds=[volume_id])[
                    "Volumes"
                ][0]
                size = volume_info["Size"]
                volumes.append({"volume_id": volume_id, "size": size})

            # Check if any volume meets criteria
            if any(volume["size"] >= min_volume_size for volume in volumes):
                instance_name = ""
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "Name":
                        instance_name = tag["Value"]

                # Sort volumes in descending order by size using itemgetter
                volumes = sorted(volumes, key=itemgetter("size"), reverse=True)
                instances.append(
                    {
                        "instance_id": instance_id,
                        "name": instance_name,
                        "volumes": volumes,
                        "standard_backup": standard_backup,
                    }
                )

    # Print the results
    if csv_format:
        # CSV output
        print("Instance Name,Instance ID,StandardBackup,", end="")
        print(",".join([f"Volume ID {i+1},Size {i+1}" for i in range(5)]))

        for instance in instances:
            volumes_output = []
            for i, volume in enumerate(instance["volumes"]):
                volumes_output.append(f"{volume['volume_id']},{volume['size']} GB")
            print(
                f"{instance['name']},{instance['instance_id']},{instance['standard_backup']},",
                end="",
            )
            print(",".join(volumes_output))
    else:
        # Standard output
        for instance in instances:
            print(
                f"Instance Name: {instance['name']}, Instance ID: {instance['instance_id']}, StandardBackup: {instance['standard_backup']}"
            )
            for volume in instance["volumes"]:
                print(f"\tVolume ID: {volume['volume_id']}, Size: {volume['size']} GB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find AWS instances with volumes of a certain size or greater."
    )
    parser.add_argument("min_volume_size", type=int, help="Minimum volume size in GB")
    parser.add_argument(
        "--filter-backup",
        choices=["True", "False"],
        help="Filter instances based on whether they are being backed up or not (StandardBackup tag value)",
    )
    parser.add_argument(
        "--csv", action="store_true", help="Output in CSV format for Google Sheets"
    )

    args = parser.parse_args()

    # Call the main function with the specified minimum volume size, filter_backup, and csv_format
    main(args.min_volume_size, args.filter_backup, args.csv)
