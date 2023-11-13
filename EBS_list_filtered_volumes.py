import argparse

import boto3


# Example usage:
# python script_name.py 10 100 --status available --encrypted False --verbose


def list_ebs_volumes(min_size, max_size, status=None, encrypted=None, verbose=False):
    # Initialize EC2 resource
    ec2 = boto3.resource("ec2")

    # Max number of filter values allowed per API call
    max_chunk_size = 195

    # Iterate through chunks
    for start_size in range(min_size, max_size + 1, max_chunk_size):
        end_size = min(start_size + max_chunk_size - 1, max_size)

        # Build filters based on the current chunk
        filters = [
            {
                "Name": "size",
                "Values": [str(size) for size in range(start_size, end_size + 1)],
            }
        ]

        # Optionally filter by status
        if status:
            filters.append({"Name": "status", "Values": [status]})

        # Optionally filter by encryption
        if encrypted is not None:
            filters.append({"Name": "encrypted", "Values": [str(encrypted).lower()]})

        # Retrieve volumes for the current chunk
        volumes = ec2.volumes.filter(Filters=filters)

        # Display volumes
        for volume in volumes:
            if verbose:
                # Detailed output
                print(f"Volume ID: {volume.id}")
                print(f"  Size: {volume.size} GiB")
                print(f"  State: {volume.state}")
                print(f"  Encrypted: {volume.encrypted}")
                print()
            else:
                # Minimal output - only volume IDs
                print(volume.id)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="List EBS volumes based on size, status, and encryption"
    )
    parser.add_argument("min_size", type=int, help="Minimum size in GiB")
    parser.add_argument("max_size", type=int, help="Maximum size in GiB")
    parser.add_argument(
        "--status", choices=["available", "in-use"], help="Status filter"
    )
    parser.add_argument(
        "--encrypted", type=str, choices=["True", "False"], help="Encryption filter"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed info")

    args = parser.parse_args()

    # Determine encryption filter
    encrypted = None
    if args.encrypted == "True":
        encrypted = True
    elif args.encrypted == "False":
        encrypted = False

    # Call the function with the provided arguments
    list_ebs_volumes(args.min_size, args.max_size, args.status, encrypted, args.verbose)


if __name__ == "__main__":
    main()
