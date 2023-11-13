import argparse

import boto3
import botocore.exceptions

"""
1. **Print Instance IPs for the Domains Listed in a File**:
   ```bash
   python script.py /path/to/input_file.txt IP
   ```
2. **Print Instance IDs for the Domains Listed in a File**:
   ```bash
   python script.py /path/to/input_file.txt ID
   ```
3. **Verbose Mode for Printing Instance IPs**:
   ```bash
   python script.py /path/to/input_file.txt IP -v
   # or
   python script.py /path/to/input_file.txt IP --verbose
   ```
4. **Verbose Mode for Printing Instance IDs**:
   ```bash
   python script.py /path/to/input_file.txt ID -v
   # or
   python script.py /path/to/input_file.txt ID --verbose
   ```
"""


# GLOBAL/CONSTANT variables
EC2_RESOURCE = boto3.resource("ec2")
EC2_CLIENT = boto3.client("ec2")
ELBV2_CLIENT = boto3.client("elbv2")


def read_domains_from_file(file_path):
    with open(file_path) as f:
        domains = [line.strip() for line in f.readlines()]
    return domains


def get_elb_listeners_arn_list():
    response = ELBV2_CLIENT.describe_load_balancers(PageSize=100)
    elb_list = response["LoadBalancers"]
    arn_list = list()

    for elb in elb_list:
        response = ELBV2_CLIENT.describe_listeners(
            LoadBalancerArn=elb["LoadBalancerArn"]
        )
        for listener in response["Listeners"]:
            arn_list.append(listener["ListenerArn"])
    return arn_list


def get_instance_public_ip(instance_id):
    instance = EC2_RESOURCE.Instance(instance_id)
    return instance.public_ip_address


def get_target_group_and_instance_id(website):
    for listener in LOAD_BALANCERS_LISTENERS_ARN_LST:
        try:
            response = ELBV2_CLIENT.describe_rules(ListenerArn=listener)
        except botocore.exceptions.BotoCoreError as e:
            print(f"Error getting rules for listener {listener}: {e}")
            continue

        rules = response["Rules"]
        counter = 0
        for rule in rules:
            counter += 1
            if counter < len(rules):
                try:
                    for value in rule["Conditions"][0]["Values"]:
                        curr_host_name = value
                        if website == curr_host_name:
                            # check if the rule is a redirect
                            if rule["Actions"][0]["Type"] == "redirect":
                                # extract the host from the redirect config
                                redirect_host = rule["Actions"][0]["RedirectConfig"][
                                    "Host"
                                ]
                                # use the redirect host to find the corresponding target group and instance id
                                return get_target_group_and_instance_id(redirect_host)
                            else:
                                if "TargetGroupArn" in rule["Actions"][0]:
                                    correct_target_group_arn = rule["Actions"][0][
                                        "TargetGroupArn"
                                    ]
                                elif "ForwardConfig" in rule["Actions"][0]:
                                    target_group_configs = rule["Actions"][0][
                                        "ForwardConfig"
                                    ]["TargetGroups"]
                                    for target_group in target_group_configs:
                                        if target_group["Weight"] == 1:
                                            correct_target_group_arn = target_group[
                                                "TargetGroupArn"
                                            ]

                                if correct_target_group_arn:
                                    response = ELBV2_CLIENT.describe_target_health(
                                        TargetGroupArn=correct_target_group_arn
                                    )
                                    instance_id = response["TargetHealthDescriptions"][
                                        0
                                    ]["Target"]["Id"]
                                    return instance_id, correct_target_group_arn
                except Exception as e:
                    print(f"An error occurred: {e}")
    print(f"No matching rule found for {website}")
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Print the instance's IP or ID")
    parser.add_argument("file", help="The input file containing the domains")
    parser.add_argument(
        "choice", choices=["IP", "ID"], help="Print either the IP or ID"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()
    input_file = args.file
    user_choice = args.choice
    verbose = args.verbose

    global LOAD_BALANCERS_LISTENERS_ARN_LST
    LOAD_BALANCERS_LISTENERS_ARN_LST = get_elb_listeners_arn_list()
    domains = read_domains_from_file(input_file)

    for domain in domains:
        instance_id, target_group_arn = get_target_group_and_instance_id(domain)
        if instance_id is None:
            print(f"No instance found for {domain}")
            continue
        if user_choice.lower() == "ip":
            instance_public_ip = get_instance_public_ip(instance_id)
            print(
                instance_public_ip if not verbose else f"{domain}, {instance_public_ip}"
            )
        elif user_choice.lower() == "id":
            print(instance_id if not verbose else f"{domain}, {instance_id}")


if __name__ == "__main__":
    main()
