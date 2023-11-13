import boto3

# gets list of services under a certain memory reservation

ECS_CLIENT = boto3.client("ecs")


def _get_clusters():
    response = ECS_CLIENT.list_clusters()
    cluster_names = []
    for arn in response["clusterArns"]:
        cluster_names.append(arn.split("/")[1])
    return cluster_names


def _describe_services():
    clusters = _get_clusters()
    for cluster in clusters:
        response = ECS_CLIENT.list_services(
            cluster=cluster,
            maxResults=30,
        )
        services = response["serviceArns"]
        if len(services) > 0:
            for service in services:
                # print(service)
                _print_memory_reservation(cluster, service)


def _print_memory_reservation(cluster, service):
    services_response = ECS_CLIENT.describe_services(
        cluster=cluster, services=[service]
    )
    if len(services_response["services"]) > 0:
        # print(services_response['services'][0])
        task_definition = services_response["services"][0]["taskDefinition"]

        tasks_response = ECS_CLIENT.describe_task_definition(
            taskDefinition=task_definition,
        )
        if len(tasks_response["taskDefinition"]["containerDefinitions"]) > 0:
            try:
                containers_defs = tasks_response["taskDefinition"][
                    "containerDefinitions"
                ]
                for container_def in containers_defs:
                    min_mem_reserv = container_def["memoryReservation"]
                    if min_mem_reserv < 6:
                        print(
                            f"Cluster {cluster} service {service} has memory reservation of {min_mem_reserv}"
                        )
            except Exception:
                pass


_describe_services()
