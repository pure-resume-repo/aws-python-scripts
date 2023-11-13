import sys
from time import sleep

import boto3


ECS_CLIENT = boto3.client("ecs")
CLUSTER = sys.argv[1]
OLD_CAPACITY_PROVIDER = sys.argv[2]
NEW_CAPACITY_PROVIDER = sys.argv[3]


def associate_new_CP():
    print(f"adding capacity provider {OLD_CAPACITY_PROVIDER} to cluster {CLUSTER}")
    ECS_CLIENT.put_cluster_capacity_providers(
        cluster=CLUSTER,
        capacityProviders=[
            NEW_CAPACITY_PROVIDER,
            OLD_CAPACITY_PROVIDER,
        ],
        defaultCapacityProviderStrategy=[
            {
                "capacityProvider": NEW_CAPACITY_PROVIDER,
                "weight": 1,
            },
        ],
    )

    print("this can take up to 2 min to show...")
    sleep(30)


def __get_ec2_services():
    response = ECS_CLIENT.list_services(
        cluster=CLUSTER,
        maxResults=30,
        launchType="EC2",
    )

    service_name_list = list()
    service_arn_list = response["serviceArns"]

    for service_arn in service_arn_list:
        split_arn = service_arn.split("/")
        service_name = split_arn[1]
        if (service_name == CLUSTER) and len(split_arn) > 2:
            service_name = split_arn[2]
        service_name_list.append(service_name)

    str = ",".join(service_name_list)
    print(f"getting service list: {str}")
    return service_name_list


def remove_service_CP_strategy():
    print(f"changing all services C.P. strategy to : {NEW_CAPACITY_PROVIDER}")

    service_name_list = __get_ec2_services()
    for service_name in service_name_list:
        ECS_CLIENT.update_service(
            cluster=CLUSTER,
            service=service_name,
            capacityProviderStrategy=[
                {
                    "capacityProvider": NEW_CAPACITY_PROVIDER,
                    "weight": 1,
                },
            ],
            forceNewDeployment=True,
        )
    print("waiting for changes to take place...")
    sleep(20)


# running functions
associate_new_CP()
remove_service_CP_strategy()
