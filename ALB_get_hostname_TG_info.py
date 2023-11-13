import sys

import boto3

# Find the TargetGroup and InstanceId in the target group for a specified domain name in
# any ALB in the Marketing account

# GLOBAL/CONSTANT variables mostly endpoints and user
EC2_CLIENT = boto3.client("ec2")
ELBV2_CLIENT = boto3.client("elbv2")

# these 2 sites are modified as they are stripped of prefix/postfix website stuff
WEBSITE = sys.argv[1]

LOAD_BALANCERS_LISTENERS_ARN_LST = []


# stripping sites of unnecessary prefix/postfix stuff
def strip_website_prefix_postfix():
    global WEBSITE
    WEBSITE = remove_prefix("https://www.", WEBSITE)
    WEBSITE = remove_prefix("http://www.", WEBSITE)
    WEBSITE = remove_prefix("https://", WEBSITE)
    WEBSITE = remove_prefix("http://", WEBSITE)
    WEBSITE = remove_prefix("www.", WEBSITE)
    WEBSITE = WEBSITE.strip("/")
    print("Stripped Website Name: " + WEBSITE + " ")


def remove_prefix(prefix, site):
    if site.startswith(prefix):
        return site[len(prefix) :]
    return site


# here we find the target group where the instance we will copy resides
def get_target_group_and_instance_id(website):
    load_balancer_counter = 1
    print("Finding website target group and Instance id.....")
    for listener in LOAD_BALANCERS_LISTENERS_ARN_LST:
        load_balancer_counter += 1
        print("checking...", str(listener))
        correct_target_group_arn = ""
        response = None

        # will skip load balancer if there is an issue
        try:
            response = ELBV2_CLIENT.describe_rules(ListenerArn=listener)
        except Exception:
            continue

        # here we traverse all the rules trying to find the website
        rules = response["Rules"]
        counter = 0
        for rule in rules:
            counter += 1
            if counter < len(rules):
                try:
                    for value in rule["Conditions"][0]["Values"]:
                        curr_host_name = value
                        if website.__eq__(curr_host_name):
                            correct_target_group_arn = rule["Actions"][0][
                                "TargetGroupArn"
                            ]

                            print(
                                "Here is the target group: ", correct_target_group_arn
                            )
                            try:
                                response = ELBV2_CLIENT.describe_target_health(
                                    TargetGroupArn=correct_target_group_arn
                                )
                                instance_id = response["TargetHealthDescriptions"][0][
                                    "Target"
                                ]["Id"]
                                print(
                                    "We have found the instance of the target group: ",
                                    instance_id,
                                )
                                return instance_id, correct_target_group_arn
                            except Exception:
                                print(
                                    "ERROR: most likely there is no registered target...."
                                )

                except KeyError:
                    # if the rule has more than 1 target group then we need this exception
                    target_group_configs = rule["Actions"][0]["ForwardConfig"][
                        "TargetGroups"
                    ]
                    for target_group in target_group_configs:
                        # we want to choose the target group where traffic goes
                        if target_group["Weight"] == 1:
                            correct_target_group_arn = target_group["TargetGroupArn"]
                            print(
                                "Here is the target group: ", correct_target_group_arn
                            )

                            response = ELBV2_CLIENT.describe_target_health(
                                TargetGroupArn=correct_target_group_arn
                            )
                            instance_id = response["TargetHealthDescriptions"][0][
                                "Target"
                            ]["Id"]
                            print(
                                "We have found the instance of the target group: ",
                                instance_id,
                            )
                            return instance_id, correct_target_group_arn
            else:
                print("Not found...Moving on to next loadbalancer\n")
    if load_balancer_counter > len(LOAD_BALANCERS_LISTENERS_ARN_LST):
        print("WE COULDN'T FIND THE WEBSITE ANYWHERE...EXITING")
        exit()


# strip site of prefix/postfix https, www, etc
strip_website_prefix_postfix()

# getting the old instance object and id##
instance_ID, target_group_ARN = get_target_group_and_instance_id(WEBSITE)
print(
    "The instance ID is: {} and the target group ARN is: {}".format(
        instance_ID, target_group_ARN
    )
)
