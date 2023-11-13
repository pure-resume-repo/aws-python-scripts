import boto3

# This script can either remove or add scale-in protection to all the instances
# inside all clusters ASGs in an account.


ECS_CLIENT = boto3.client("ecs")
ASG_CLIENT = boto3.client("autoscaling")


def _get_clusters():
    response = ECS_CLIENT.list_clusters()
    cluster_names = []
    for arn in response["clusterArns"]:
        cluster_names.append(arn.split("/")[1])
    return cluster_names


def _get_capacity_providers():
    clusters = _get_clusters()
    response = ECS_CLIENT.describe_clusters(clusters=clusters)

    cluster_obj_list = response["clusters"]
    capacity_providers = list()

    for cluster_obj in cluster_obj_list:
        capacity_providers.append(cluster_obj["capacityProviders"])
    return capacity_providers


def _get_cp_asg():
    capacity_providers = _get_capacity_providers()
    new_cp_list = list()

    for capacity_provider in capacity_providers:
        if len(capacity_provider) > 0:
            new_cp_list.append(capacity_provider[0])

    capacity_providers = (",".join(new_cp_list)).split(",")

    response = ECS_CLIENT.describe_capacity_providers(
        capacityProviders=capacity_providers,
    )

    x = 0
    asg_lst = list()
    for res in response["capacityProviders"]:
        asg_arn = response["capacityProviders"][x]["autoScalingGroupProvider"][
            "autoScalingGroupArn"
        ]
        asg_name = asg_arn.split("/")
        asg_lst.append(asg_name[1])

        x += 1
    return asg_lst


def _set_scalein_protection(scale_in_protection):
    asg_list = _get_cp_asg()
    response = ASG_CLIENT.describe_auto_scaling_groups(AutoScalingGroupNames=asg_list)

    asg_list_objects = response["AutoScalingGroups"]
    for asg_obj in asg_list_objects:
        instances = asg_obj["Instances"]
        instance_list = list()

        for instance in instances:
            instance_id = instance["InstanceId"]
            instance_list.append(instance_id)

            ASG_CLIENT.set_instance_protection(
                InstanceIds=instance_list,
                AutoScalingGroupName=asg_obj["AutoScalingGroupName"],
                ProtectedFromScaleIn=scale_in_protection,
            )


def main():
    scale_in_protection = input(
        "Set scale-in protection for all cluster instances as True or False:\n"
    )
    if scale_in_protection.lower() == "true":
        print("adding scale in protection, please wait...")
        _set_scalein_protection(True)
        print("ADDED")

    elif scale_in_protection.lower() == "false":
        print("removing scale in protection, please wait...")
        _set_scalein_protection(False)
        print("REMOVED")


main()
