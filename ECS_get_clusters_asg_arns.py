import boto3

# The script will return the auto-scaling group ARNs for all clusters in an account.

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


def _get_cp_asg_arn_list():
    capacity_providers = _get_capacity_providers()
    new_cp_list = list()

    for capacity_provider in capacity_providers:
        if len(capacity_provider) > 0:
            new_cp_list.append(capacity_provider[0])

    capacity_providers = (",".join(new_cp_list)).split(",")

    response = ECS_CLIENT.describe_capacity_providers(
        capacityProviders=capacity_providers,
    )

    asg_arn_list = list()
    for res in response["capacityProviders"]:
        asg_arn = res["autoScalingGroupProvider"]["autoScalingGroupArn"]
        asg_arn_list.append(asg_arn)

    return asg_arn_list


print(_get_cp_asg_arn_list())
