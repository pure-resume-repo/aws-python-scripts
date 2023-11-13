import argparse

import boto3


def get_forecast_cost_and_usage(
    client, start_date, end_date, granularity, tag_key, tag_value, region
):
    response = client.get_cost_forecast(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity=granularity,
        Metric="UNBLENDED_COST",
        Filter={"Tags": {"Key": tag_key, "Values": [tag_value]}},
    )
    return response["Total"]["Amount"], response["Total"]["Unit"]


def get_usage_cost(
    client, start_date, end_date, granularity, tag_key, tag_value, region
):
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity=granularity,
        Metrics=["UnblendedCost"],
        Filter={"Tags": {"Key": tag_key, "Values": [tag_value]}},
    )
    return response["ResultsByTime"]


def main():
    parser = argparse.ArgumentParser(description="Fetch AWS cost data based on tags")
    parser.add_argument("--start_date", required=True, help="Start date for the data")
    parser.add_argument("--end_date", required=True, help="End date for the data")
    parser.add_argument(
        "--granularity",
        choices=["DAILY", "MONTHLY", "HOURLY"],
        required=True,
        help="Granularity of the data",
    )
    parser.add_argument("--region", default="us-west-2", help="AWS region")
    parser.add_argument("--tag_key", required=True, help="Tag key to filter on")
    parser.add_argument("--tag_value", required=True, help="Tag value to filter on")
    parser.add_argument(
        "--type",
        choices=["usage", "forecast"],
        required=True,
        help="Type of data: usage or forecast",
    )

    args = parser.parse_args()

    client = boto3.client("ce", region_name=args.region)

    if args.type == "forecast":
        amount, unit = get_forecast_cost_and_usage(
            client,
            args.start_date,
            args.end_date,
            args.granularity,
            args.tag_key,
            args.tag_value,
            args.region,
        )
        print(
            f"Forecasted cost from {args.start_date} to {args.end_date} is {amount} {unit}"
        )

    elif args.type == "usage":
        usage_data = get_usage_cost(
            client,
            args.start_date,
            args.end_date,
            args.granularity,
            args.tag_key,
            args.tag_value,
            args.region,
        )
        for item in usage_data:
            period = item["TimePeriod"]
            total = item["Total"]["UnblendedCost"]
            print(
                f"Cost from {period['Start']} to {period['End']} is {total['Amount']} {total['Unit']}"
            )


if __name__ == "__main__":
    main()
