import argparse
import time

import boto3

# Create the Boto3 clients for autoscaling
autoscaling_client = boto3.client("autoscaling")


def get_launch_configuration_name(asg_name):
    response = autoscaling_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name]
    )
    try:
        return response["AutoScalingGroups"][0]["LaunchConfigurationName"]
    except KeyError:
        print(f"No Launch Configuration found for Auto Scaling group: {asg_name}")
        return None


def update_autoscaling_group_to_use_launch_template(asg_name, launch_template_name):
    try:
        autoscaling_client.update_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            LaunchTemplate={"LaunchTemplateName": launch_template_name, "Version": "1"},
        )
        print("Updated Auto Scaling group to use Launch Template.")
        return True
    except Exception as e:
        print(f"Failed to update Auto Scaling group: {e}")
        return False


def replace_instances_in_autoscaling_group(asg_name):
    try:
        response = autoscaling_client.start_instance_refresh(
            AutoScalingGroupName=asg_name,
            Strategy="Rolling",
            Preferences={"MinHealthyPercentage": 65, "InstanceWarmup": 300},
        )
        print("Started instance refresh in Auto Scaling group.")
        return response["InstanceRefreshId"]
    except Exception as e:
        print(f"Failed to start instance refresh: {e}")


def check_instance_refresh_status(asg_name, refresh_id):
    while True:
        response = autoscaling_client.describe_instance_refreshes(
            AutoScalingGroupName=asg_name,
            InstanceRefreshIds=[refresh_id],
        )
        refresh_details = response["InstanceRefreshes"][0]
        status = refresh_details["Status"]

        # Check if 'PercentageComplete' key exists in the dictionary before accessing it
        percentage_complete = refresh_details.get("PercentageComplete", "N/A")

        instances_to_update = refresh_details.get("InstancesToUpdate", "N/A")
        print(
            f"Instance refresh status: {status}, Percentage complete: {percentage_complete}%, Instances remaining to update: {instances_to_update}"
        )

        if status == "Successful":
            break
        time.sleep(15)


def remove_instance_protection(asg_name):
    # get instances in the ASG
    response = autoscaling_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name]
    )
    instances = response["AutoScalingGroups"][0]["Instances"]

    # prepare list of instances
    instance_ids = [instance["InstanceId"] for instance in instances]

    # remove protection
    try:
        autoscaling_client.set_instance_protection(
            AutoScalingGroupName=asg_name,
            InstanceIds=instance_ids,
            ProtectedFromScaleIn=False,
        )
        print("Removed instance protection for all instances.")
    except Exception as e:
        print(f"Failed to remove instance protection: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Updates an Auto Scaling group to use a launch template and replace instances"
    )
    parser.add_argument("asg_name", help="The name of the Auto Scaling group")
    args = parser.parse_args()

    launch_template_name = get_launch_configuration_name(args.asg_name)
    if launch_template_name is not None:
        update_success = update_autoscaling_group_to_use_launch_template(
            args.asg_name, launch_template_name
        )
        if update_success:
            remove_instance_protection(args.asg_name)  # Remove instance protection
            refresh_id = replace_instances_in_autoscaling_group(args.asg_name)
            if refresh_id is not None:
                check_instance_refresh_status(args.asg_name, refresh_id)


if __name__ == "__main__":
    main()
