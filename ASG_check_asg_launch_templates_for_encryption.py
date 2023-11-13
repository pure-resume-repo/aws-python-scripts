import argparse

import boto3


def check_launch_configuration_encryption(
    launch_configuration_name, autoscaling_client
):
    """
    Check encryption of EBS volumes in a given launch configuration.
    Returns True if unencrypted volumes are found, False otherwise.
    """
    launch_config = autoscaling_client.describe_launch_configurations(
        LaunchConfigurationNames=[launch_configuration_name]
    )["LaunchConfigurations"][0]

    for block_device_mapping in launch_config["BlockDeviceMappings"]:
        ebs = block_device_mapping.get("Ebs")
        if ebs and not ebs.get("Encrypted", False):
            return True
    return False


def check_launch_template_encryption(launch_template_id, version, ec2_client):
    """
    Check encryption of EBS volumes in a given launch template version.
    Returns True if unencrypted volumes are found, False otherwise.
    """
    versions = ec2_client.describe_launch_template_versions(
        LaunchTemplateId=launch_template_id, Versions=[version]
    )

    for latest_version in versions["LaunchTemplateVersions"]:
        for block_device_mapping in latest_version["LaunchTemplateData"][
            "BlockDeviceMappings"
        ]:
            ebs = block_device_mapping.get("Ebs")
            if ebs and not ebs.get("Encrypted", False):
                return True
    return False


# Argument parser
parser = argparse.ArgumentParser(
    description="Check AWS resources for unencrypted volumes"
)
parser.add_argument(
    "--check-all-templates", action="store_true", help="Check all launch templates"
)
parser.add_argument(
    "--check-all-configurations",
    action="store_true",
    help="Check all launch configurations",
)
parser.add_argument(
    "--all-versions", action="store_true", help="Check all versions of launch templates"
)
args = parser.parse_args()

# Initialize clients
autoscaling_client = boto3.client("autoscaling")
ec2_client = boto3.client("ec2")

# Check all Auto Scaling Groups
print("Checking Auto Scaling Groups:")
paginator = autoscaling_client.get_paginator("describe_auto_scaling_groups")
for page in paginator.paginate():
    for asg in page["AutoScalingGroups"]:
        # Check Launch Configuration
        unencrypted_found = False
        if asg.get("LaunchConfigurationName"):
            unencrypted_found = check_launch_configuration_encryption(
                asg["LaunchConfigurationName"], autoscaling_client
            )

        # Check Launch Template
        if asg.get("LaunchTemplate") and not unencrypted_found:
            launch_template = asg["LaunchTemplate"]
            unencrypted_found = check_launch_template_encryption(
                launch_template["LaunchTemplateId"],
                launch_template["Version"],
                ec2_client,
            )

        if unencrypted_found:
            num_instances = len(asg["Instances"])
            print(
                f"Auto Scaling Group: {asg['AutoScalingGroupName']} does not have encrypted storage volumes. Number of instances: {num_instances}"
            )

# Check all Launch Configurations if specified
if args.check_all_configurations:
    print("\nChecking all Launch Configurations:")
    for lc in autoscaling_client.describe_launch_configurations()[
        "LaunchConfigurations"
    ]:
        if check_launch_configuration_encryption(
            lc["LaunchConfigurationName"], autoscaling_client
        ):
            print(
                f"  Launch Configuration: {lc['LaunchConfigurationName']} does not have encrypted storage volumes."
            )

# Check all Launch Templates if specified
if args.check_all_templates:
    print("\nChecking all Launch Templates:")
    for lt in ec2_client.describe_launch_templates()["LaunchTemplates"]:
        launch_template_id = lt["LaunchTemplateId"]

        if args.all_versions:
            # Check all versions
            for version in ec2_client.describe_launch_template_versions(
                LaunchTemplateId=launch_template_id
            )["LaunchTemplateVersions"]:
                if check_launch_template_encryption(
                    launch_template_id, str(version["VersionNumber"]), ec2_client
                ):
                    print(
                        f"  Launch Template: {launch_template_id}, Version: {version['VersionNumber']} does not have encrypted storage volumes."
                    )
        else:
            # Check only the latest version
            if check_launch_template_encryption(
                launch_template_id, "$Latest", ec2_client
            ):
                print(
                    f"  Launch Template: {launch_template_id} (latest version) does not have encrypted storage volumes."
                )
