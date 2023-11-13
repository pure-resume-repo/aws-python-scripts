import argparse

import boto3


def get_volumes_info(volumes_list, tag_key=None, filter_tag=None):
    ec2 = boto3.resource("ec2")

    with open(volumes_list) as f:
        volumes = f.read().splitlines()

    for volume_id in volumes:
        volume = ec2.Volume(volume_id)
        tags = {t["Key"]: t["Value"] for t in volume.tags or []}

        if filter_tag:
            key, value = filter_tag.split("=")
            if tags.get(key) != value:
                continue

        if tag_key:
            print(f"Volume ID: {volume_id}, Tag - {tag_key}: {tags.get(tag_key)}")
        else:
            print(f"Volume ID: {volume_id}, Tags: {tags}")


def main():
    parser = argparse.ArgumentParser(
        description="Process AWS EBS volumes and print tags"
    )
    parser.add_argument("--volumes", required=True, help="File with volume IDs")
    parser.add_argument("--tag", help="Specific tag to print")
    parser.add_argument("--filter", help="Filter tag in format key=value")

    args = parser.parse_args()
    get_volumes_info(args.volumes, args.tag, args.filter)


if __name__ == "__main__":
    main()
