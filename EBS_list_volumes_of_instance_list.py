import argparse

import boto3


def get_volume_ids(instance_ids):
    ec2 = boto3.resource("ec2")

    for instance_id in instance_ids:
        instance = ec2.Instance(instance_id)
        print(f"Instance ID: {instance_id}")
        for volume in instance.volumes.all():
            print(f"  Volume ID: {volume.id}")


def main():
    parser = argparse.ArgumentParser(
        description="Prints the volume IDs of the provided AWS instances."
    )
    parser.add_argument(
        "instances",
        type=str,
        help="A file containing the list of AWS instance IDs, one per line.",
    )

    args = parser.parse_args()

    with open(args.instances) as file:
        instance_ids = file.read().strip().split("\n")

    get_volume_ids(instance_ids)


if __name__ == "__main__":
    main()
