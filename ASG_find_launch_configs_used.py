import argparse

import boto3

# Define the AWS resources
ecs = boto3.client("ecs")
autoscaling = boto3.client("autoscaling")

# Argparse setup
parser = argparse.ArgumentParser(description="Find ASGs with Launch Configurations")
parser.add_argument(
    "--running",
    action="store_true",
    help="Find all ASGs with running instances, regardless of ECS",
)
args = parser.parse_args()


def get_asg_capacity_providers():
    # Define a dictionary to store ASG with capacity providers
    asg_capacity_providers = {}

    # Get list of all capacity providers
    providers = ecs.describe_capacity_providers()["capacityProviders"]

    for provider in providers:
        if "autoScalingGroupProvider" in provider:
            asg_name = provider["autoScalingGroupProvider"][
                "autoScalingGroupArn"
            ].split("/")[-1]
            asg_capacity_providers[asg_name] = provider["name"]

    return asg_capacity_providers


def main():
    asg_capacity_providers = get_asg_capacity_providers()

    if args.running:
        # Get list of all ASGs
        response = autoscaling.describe_auto_scaling_groups()
        asgs = [asg for asg in response["AutoScalingGroups"] if asg["Instances"]]
        clusters = ["N/A"] * len(asgs)  # No specific cluster

    else:
        # Get list of all ECS clusters
        clusters_arns = ecs.list_clusters()["clusterArns"]

        asgs = []
        clusters = []
        for cluster_arn in clusters_arns:
            # Get list of capacity providers for this cluster
            cluster_capacity_providers = ecs.describe_clusters(clusters=[cluster_arn])[
                "clusters"
            ][0]["capacityProviders"]

            # Get list of all ASGs
            response = autoscaling.describe_auto_scaling_groups()

            for asg in response["AutoScalingGroups"]:
                # Check if the ASG is used as a capacity provider in this cluster
                if (
                    asg["AutoScalingGroupName"] in asg_capacity_providers.keys()
                    and asg_capacity_providers[asg["AutoScalingGroupName"]]
                    in cluster_capacity_providers
                ):
                    asgs.append(asg)
                    clusters.append(
                        cluster_arn.split("/")[-1]
                    )  # Append the cluster name

    for asg, cluster in zip(asgs, clusters):
        if "LaunchConfigurationName" in asg:
            print(
                f'\n---- Auto Scaling Group ----\nName: {asg["AutoScalingGroupName"]}\nLaunch Configuration: {asg["LaunchConfigurationName"]}\nCluster: {cluster}\n'
            )


if __name__ == "__main__":
    main()
