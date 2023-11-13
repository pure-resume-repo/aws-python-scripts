import argparse
import logging

import boto3
import botocore.exceptions

# Configure logging settings
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Initialize AWS service clients
EC2_RESOURCE = boto3.resource("ec2")
EC2_CLIENT = boto3.client("ec2")
ELBV2_CLIENT = boto3.client("elbv2")


def read_domains_from_file(file_path):
    """Read domains from a file and return them as a list."""
    try:
        with open(file_path) as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        logging.error("File not found.")
        raise


def get_elb_listeners_arn_list():
    """Retrieve Listener ARNs for all load balancers."""
    response = ELBV2_CLIENT.describe_load_balancers(PageSize=100)
    arn_list = []
    for elb in response["LoadBalancers"]:
        listeners_response = ELBV2_CLIENT.describe_listeners(
            LoadBalancerArn=elb["LoadBalancerArn"]
        )
        for listener in listeners_response["Listeners"]:
            arn_list.append(listener["ListenerArn"])
    return arn_list


def get_volumes(instance_id):
    """Get volume IDs associated with an EC2 instance."""
    instance = EC2_RESOURCE.Instance(instance_id)
    return [volume.id for volume in instance.volumes.all()]


def tag_instance_and_volumes(instance_id, website):
    """Tag the EC2 instance and its associated volumes."""
    tags = [{"Key": "WebsiteURL", "Value": website}]
    EC2_CLIENT.create_tags(Resources=[instance_id], Tags=tags)
    for volume_id in get_volumes(instance_id):
        EC2_CLIENT.create_tags(Resources=[volume_id], Tags=tags)


def get_target_group_and_instance_id(website):
    """Get target group and instance ID based on a website."""
    for listener in LOAD_BALANCERS_LISTENERS_ARN_LIST:
        try:
            response = ELBV2_CLIENT.describe_rules(ListenerArn=listener)
        except botocore.exceptions.BotoCoreError as e:
            logging.error(f"Error getting rules for listener {listener}: {e}")
            continue

        for rule in response.get("Rules", []):
            conditions = rule.get("Conditions", [])
            if not conditions:
                continue
            values = conditions[0].get("Values", [])
            if not values:
                continue

            for value in values:
                if website == value:
                    correct_target_group_arn = None
                    if rule["Actions"][0]["Type"] == "redirect":
                        redirect_host = rule["Actions"][0]["RedirectConfig"]["Host"]
                        return get_target_group_and_instance_id(redirect_host)

                    if "TargetGroupArn" in rule["Actions"][0]:
                        correct_target_group_arn = rule["Actions"][0]["TargetGroupArn"]
                    elif "ForwardConfig" in rule["Actions"][0]:
                        target_group_configs = rule["Actions"][0]["ForwardConfig"][
                            "TargetGroups"
                        ]
                        for target_group in target_group_configs:
                            if target_group["Weight"] == 1:
                                correct_target_group_arn = target_group[
                                    "TargetGroupArn"
                                ]

                    if correct_target_group_arn:
                        response = ELBV2_CLIENT.describe_target_health(
                            TargetGroupArn=correct_target_group_arn
                        )
                        instance_id = response["TargetHealthDescriptions"][0]["Target"][
                            "Id"
                        ]
                        return instance_id, correct_target_group_arn

    logging.info(f"No matching rule found for {website}")
    return None, None


def main():
    """Main function: Entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Tag EC2 instances and their associated volumes based on URLs from a file."
    )
    parser.add_argument("file", help="File containing the list of domains.")
    args = parser.parse_args()

    global LOAD_BALANCERS_LISTENERS_ARN_LIST
    LOAD_BALANCERS_LISTENERS_ARN_LIST = get_elb_listeners_arn_list()

    domains = read_domains_from_file(args.file)
    to_be_tagged = []

    for domain in domains:
        instance_id, _ = get_target_group_and_instance_id(domain)
        if instance_id:
            volume_ids = get_volumes(instance_id)
            logging.info(f"Found: Instance ID: {instance_id}, Volumes: {volume_ids}")
            to_be_tagged.append((instance_id, domain))

    if to_be_tagged:
        confirm = input(
            "The following resources will be tagged. Do you want to proceed? [y/N]: "
        )
        if confirm.lower() in ("y", "yes"):
            for instance_id, domain in to_be_tagged:
                tag_instance_and_volumes(instance_id, domain)
                logging.info(
                    f"Instance {instance_id} and its volumes have been tagged."
                )
    else:
        logging.info("No instances found for the provided domains.")


if __name__ == "__main__":
    main()
