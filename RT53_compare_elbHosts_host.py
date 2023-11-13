import boto3

# This script finds the host names in rule of the load balancers and checks to see if they exist in Route 53 the same account.
ELB_CLIENT = boto3.client("elbv2")
RT53_CLIENT = boto3.client("route53")


# Get a list of load balancer host names in all rules and all listeners
def get_elb_hosts_list():
    response = ELB_CLIENT.describe_load_balancers(PageSize=100)
    elb_list = response["LoadBalancers"]
    hosts_list = list()

    for elb in elb_list:
        response = ELB_CLIENT.describe_listeners(LoadBalancerArn=elb["LoadBalancerArn"])
        for listener in response["Listeners"]:
            response = ELB_CLIENT.describe_rules(ListenerArn=listener["ListenerArn"])
            for rule in response["Rules"]:
                for condition in rule["Conditions"]:
                    for value in condition["Values"]:
                        # performing stripping
                        value = remove_prefix("https://www.", value)
                        value = remove_prefix("http://www.", value)
                        value = remove_prefix("https://", value)
                        value = remove_prefix("http://", value)
                        value = remove_prefix("www.", value)
                        value = value.strip("/")
                        hosts_list.append(value.lower().strip())
    return hosts_list


# Get a list of Route 53 A records
def get_rt53_records_list():
    response = RT53_CLIENT.list_hosted_zones(MaxItems="100")
    hosted_zones_list = response["HostedZones"]
    host_list = list()

    for hosted_zone in hosted_zones_list:
        zone_id = hosted_zone["Id"].split("/")[-1]
        response = RT53_CLIENT.list_resource_record_sets(HostedZoneId=zone_id)
        resource_record_sets = response["ResourceRecordSets"]
        for record in resource_record_sets:
            host_list.append(record["Name"][:-1].lower().strip())
    return host_list


def remove_prefix(prefix, site):
    if site.startswith(prefix):
        return site[len(prefix) :]
    return site


# Compare host name from elb to rt53 record name
def compare_elb_rt53():
    elb_host_list = get_elb_hosts_list()
    rt53_host_list = get_rt53_records_list()
    found_count = 0
    not_found_count = 0

    # Comparison
    for host in elb_host_list:
        if host not in rt53_host_list:
            print(host)
            not_found_count += 1
        else:
            found_count += 1
    print(f"Found: {found_count} \n Not Found: {not_found_count}")


compare_elb_rt53()
