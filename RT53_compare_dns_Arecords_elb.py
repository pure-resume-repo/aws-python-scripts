import boto3

# This script finds the DNS names of the load balancers and checks to see if they exist in Route 53 the same account.
ELB_CLIENT = boto3.client("elbv2")
RT53_CLIENT = boto3.client("route53")


# Get a list of load balancer DNS names
def get_elb_dns_list():
    response = ELB_CLIENT.describe_load_balancers(PageSize=100)
    elb_list = response["LoadBalancers"]
    dsn_list = [elb["DNSName"] for elb in elb_list]
    return dsn_list


# Get a list of Route 53 A records
def get_rt53_records_list():
    response = RT53_CLIENT.list_hosted_zones(MaxItems="100")
    hosted_zones_list = response["HostedZones"]
    dns_records_list = list()

    for hosted_zone in hosted_zones_list:
        zone_id = hosted_zone["Id"].split("/")[-1]
        response = RT53_CLIENT.list_resource_record_sets(HostedZoneId=zone_id)
        resource_record_sets = response["ResourceRecordSets"]

        for record in resource_record_sets:
            try:
                if "AliasTarget" in record:
                    dns_name = record["AliasTarget"]["DNSName"]
                    dns_records_list.append(dns_name)
            except Exception as e:
                print(f"An error occurred: {e}")

    return dns_records_list


# Compare ELB DNS name to A records
def compare_elb_rt53_dns():
    elb_dns_list = get_elb_dns_list()
    rt53_dns_list = [
        dns_record[:-1].strip().lower().replace("dualstack.", "")
        for dns_record in get_rt53_records_list()
    ]

    # Comparison
    for dns in elb_dns_list:
        dns = dns.strip().lower()
        if dns not in rt53_dns_list:
            print(dns)


compare_elb_rt53_dns()
