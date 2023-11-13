import argparse

import boto3

# The purpose of the script is to find the target group and the load balancer that an EC2 instance belongs to


# Function to search for an EC2 instance in all load balancers and target groups
def search_instance_in_load_balancers(instance_id):
    # Create boto3 client for Elastic Load Balancing
    elbv2_client = boto3.client("elbv2")

    # Get the list of load balancers
    load_balancers = elbv2_client.describe_load_balancers()

    # Flag to indicate if the instance was found
    instance_found = False

    # Iterate through each load balancer
    for load_balancer in load_balancers["LoadBalancers"]:
        load_balancer_arn = load_balancer["LoadBalancerArn"]
        load_balancer_name = load_balancer["LoadBalancerName"]

        # Get the target groups for this load balancer
        target_groups = elbv2_client.describe_target_groups(
            LoadBalancerArn=load_balancer_arn
        )

        # Iterate through each target group
        for target_group in target_groups["TargetGroups"]:
            target_group_arn = target_group["TargetGroupArn"]
            target_group_name = target_group["TargetGroupName"]

            # Get the health descriptions for targets in this target group
            target_health_descriptions = elbv2_client.describe_target_health(
                TargetGroupArn=target_group_arn
            )

            # Iterate through each target health description
            for target_health_desc in target_health_descriptions[
                "TargetHealthDescriptions"
            ]:
                target = target_health_desc["Target"]
                target_id = target["Id"]

                # Check if the target is the instance we are looking for
                if target_id == instance_id:
                    print(
                        f"EC2 instance ID {target_id} is part of the load balancer "
                        f"{load_balancer_name} and target group {target_group_name}"
                    )
                    instance_found = True

    # Print a message if the instance was not found in any target group of any load balancer
    if not instance_found:
        print(
            f"EC2 instance ID {instance_id} was not found in any target group of any load balancer."
        )


# Main function to parse command-line arguments and initiate search
def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description="Search for an EC2 instance in all AWS Load Balancers and Target Groups."
    )

    # Add argument for instance ID
    parser.add_argument("instance_id", help="The ID of the EC2 instance to search for.")

    # Parse command-line arguments
    args = parser.parse_args()

    # Search for the instance in load balancers and target groups
    search_instance_in_load_balancers(args.instance_id)


# Execute the main function if the script is run as a standalone program
if __name__ == "__main__":
    main()
