import argparse

import boto3


# The purpose of the script is to specify a port and find
# out if there is a security group that allows inbound
# access to that port
def find_security_groups(port, only_ids):
    # Create a client for the EC2 service
    ec2 = boto3.client("ec2")

    # Get all security groups
    response = ec2.describe_security_groups()

    # Iterate over all security groups
    for sg in response["SecurityGroups"]:
        # Check the inbound rules for each security group
        for permission in sg["IpPermissions"]:
            # Check if the rule allows all protocols and hence all ports
            ip_protocol = permission.get("IpProtocol", None)
            from_port = permission.get("FromPort", None)
            to_port = permission.get("ToPort", None)

            # Check for All Traffic Rule or if the port number falls within the range
            if ip_protocol == "-1" or (
                from_port is not None
                and to_port is not None
                and (
                    from_port == 0 and to_port == 65535 or from_port <= port <= to_port
                )
            ):
                # If the only_ids flag is set, only print the security group ID
                if only_ids:
                    print(sg["GroupId"])
                else:
                    # Else, print all details
                    print("\nSecurity Group Details:")
                    print(f"   Group Name: {sg['GroupName']}")
                    print(f"   Group ID: {sg['GroupId']}")
                    print(f"   Description: {sg['Description']}")
                    if ip_protocol == "-1":
                        print("   Allows All Access on all ports")
                    else:
                        print(
                            "   Allows All Access on all TCP ports"
                        ) if from_port == 0 and to_port == 65535 else print(
                            f"   Allows inbound access on port {port}"
                        )


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Check which security groups allow inbound access on a specific port or all ports."
    )
    parser.add_argument("port", type=int, help="The port to check for access.")
    # Add new argument for only printing IDs
    parser.add_argument(
        "--only-ids", action="store_true", help="Only display the security group IDs."
    )
    args = parser.parse_args()

    # Call the function with the specified port and only_ids flag
    find_security_groups(args.port, args.only_ids)
