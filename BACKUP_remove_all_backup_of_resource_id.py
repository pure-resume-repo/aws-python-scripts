import boto3

arns = []


ec2 = boto3.client("ec2")
backup_client = boto3.client("backup")


def get_instance_id_from_arn(arn):
    return arn.split("/")[-1]


def get_instance_name(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    for instance in response["Reservations"][0]["Instances"]:
        for tag in instance["Tags"]:
            if tag["Key"] == "Name":
                return tag["Value"]
    return None


def list_backups(instance_id):
    response = backup_client.list_recovery_points_by_resource(
        ResourceArn=f"arn:aws:ec2:us-west-2:1234566634:instance/{instance_id}"
    )
    return response["RecoveryPoints"]


for arn in arns:
    instance_id = get_instance_id_from_arn(arn)
    instance_name = get_instance_name(instance_id)
    backups = list_backups(instance_id)

    print(f"Backups for {arn} ({instance_id}), Resource Name: {instance_name}:")
    total_backups = len(backups)
    print(f"  Total Backups: {total_backups}")

    for backup in backups:
        print(
            f"    Backup ARN: {backup['RecoveryPointArn']}, Created at: {backup['CreationDate']}"
        )

    if total_backups > 0:
        confirm = (
            input(
                f"Do you want to delete all {total_backups} backups for instance '{instance_name}'? (yes/no): "
            )
            .strip()
            .lower()
        )
        if confirm == "yes":
            for backup in backups:
                backup_arn = backup["RecoveryPointArn"]
                print(f"Deleting backup {backup_arn}")
                backup_client.delete_recovery_point(
                    BackupVaultName=backup["BackupVaultName"],
                    RecoveryPointArn=backup_arn,
                )
            print("All backups deleted.")
        else:
            print("Operation canceled.")

    proceed = (
        input("Do you want to continue to the next instance? (yes/no): ")
        .strip()
        .lower()
    )
    if proceed != "yes":
        break
