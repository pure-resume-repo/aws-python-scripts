import argparse
import csv

import boto3


def get_execution_info(execution_id, ssm_client):
    response = ssm_client.get_automation_execution(AutomationExecutionId=execution_id)

    failed_steps = []
    pending_steps = []
    volume_ids = ""
    instance_id = ""

    for step in response["AutomationExecution"].get("StepExecutions", []):
        step_name = step["StepName"]
        step_status = step["StepStatus"]
        if step_status == "TimedOut":
            failed_steps.append(step_name)
        elif step_status == "Pending":
            pending_steps.append(step_name)

        if step_name == "describeVolume":
            volume_ids_raw = step["Inputs"]["VolumeIds"]
            if isinstance(volume_ids_raw, str):
                try:
                    volume_ids_list = eval(volume_ids_raw)
                    if isinstance(volume_ids_list, list):
                        volume_ids = ", ".join(volume_ids_list)
                except SyntaxError:
                    volume_ids = volume_ids_raw
            else:
                volume_ids = ", ".join(volume_ids_raw)

            instance_id = ",".join(step["Outputs"]["instanceId"])

    return {
        "ExecutionID": execution_id,
        "FailedSteps": ", ".join(failed_steps),
        "PendingSteps": ", ".join(pending_steps),
        "VolumeID": volume_ids,
        "InstanceID": instance_id,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Check AWS Systems Manager Automation Execution Status"
    )
    parser.add_argument(
        "execution_ids", help="File with list of Execution IDs, one per line", type=str
    )
    parser.add_argument("--csv", help="Output in CSV format", action="store_true")
    args = parser.parse_args()

    ssm_client = boto3.client("ssm")

    if args.csv:
        with open("output.csv", "w", newline="") as csvfile:
            fieldnames = [
                "ExecutionID",
                "FailedSteps",
                "PendingSteps",
                "VolumeID",
                "InstanceID",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            with open(args.execution_ids) as file:
                for execution_id in file:
                    execution_id = execution_id.strip()
                    info = get_execution_info(execution_id, ssm_client)
                    writer.writerow(info)
    else:
        with open(args.execution_ids) as file:
            for execution_id in file:
                execution_id = execution_id.strip()
                info = get_execution_info(execution_id, ssm_client)
                print(f"Execution ID: {info['ExecutionID']}")
                print(f"Failed Steps: {info['FailedSteps']}")
                print(f"Pending Steps: {info['PendingSteps']}")
                print(f"Volume ID: {info['VolumeID']}")
                print(f"Instance ID: {info['InstanceID']}\n")


if __name__ == "__main__":
    main()
