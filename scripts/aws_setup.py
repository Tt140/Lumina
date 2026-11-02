"""LuminaLab Swarm - AWS Setup Script for DynamoDB & S3."""

import os
from typing import Any
from src.config import get_config


def create_dynamo_table(config: Any = None) -> dict[str, str]:
    """
    Creates DynamoDB table for impact ledger. If already exists -> skips.

    Returns:
        {"table_name": str, "status": "created" | "already_exists" | "mock_skipped", "arn": str}
    """
    cfg = config or get_config()
    table_name = cfg.DYNAMO_TABLE_NAME

    if cfg.LUMINA_MOCK_MODE:
        print(f"[MOCK] Skipping DynamoDB table creation for '{table_name}'")
        return {"table_name": table_name, "status": "mock_skipped", "arn": "mock"}

    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client("dynamodb", region_name=cfg.AWS_REGION)
        try:
            response = client.create_table(
                TableName=table_name,
                KeySchema=[{"AttributeName": "session_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "session_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )
            arn = response.get("TableDescription", {}).get("TableArn", "")
            return {"table_name": table_name, "status": "created", "arn": arn}
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ResourceInUseException":
                return {"table_name": table_name, "status": "already_exists", "arn": ""}
            raise
    except Exception as e:
        return {"table_name": table_name, "status": f"failed: {e}", "arn": ""}


def create_s3_bucket(config: Any = None) -> dict[str, str]:
    """
    Creates S3 bucket for labs. If already exists -> skips.

    Returns:
        {"bucket_name": str, "status": "created" | "already_exists" | "mock_skipped"}
    """
    cfg = config or get_config()
    bucket_name = cfg.S3_BUCKET_NAME

    if cfg.LUMINA_MOCK_MODE:
        print(f"[MOCK] Skipping S3 bucket creation for '{bucket_name}'")
        return {"bucket_name": bucket_name, "status": "mock_skipped"}

    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client("s3", region_name=cfg.AWS_REGION)
        kwargs: dict[str, Any] = {"Bucket": bucket_name}
        if cfg.AWS_REGION != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": cfg.AWS_REGION}

        try:
            client.create_bucket(**kwargs)
            return {"bucket_name": bucket_name, "status": "created"}
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
                return {"bucket_name": bucket_name, "status": "already_exists"}
            raise
    except Exception as e:
        return {"bucket_name": bucket_name, "status": f"failed: {e}"}


def run_setup() -> dict[str, Any]:
    """
    Executes full infrastructure setup: DynamoDB + S3.

    Returns:
        {"dynamo": dict, "s3": dict, "mock_mode": bool}
    """
    cfg = get_config()
    print("╔══════════════════════════════════════╗")
    print("║   LuminaLab Swarm — AWS Setup       ║")
    print("╚══════════════════════════════════════╝")
    print(f"Region: {cfg.AWS_REGION} | Mock Mode: {cfg.LUMINA_MOCK_MODE}")

    dynamo_result = create_dynamo_table(cfg)
    print(f"DynamoDB: {dynamo_result['table_name']} -> {dynamo_result['status']}")

    s3_result = create_s3_bucket(cfg)
    print(f"S3 Bucket: {s3_result['bucket_name']} -> {s3_result['status']}")

    return {
        "dynamo": dynamo_result,
        "s3": s3_result,
        "mock_mode": cfg.LUMINA_MOCK_MODE,
    }


if __name__ == "__main__":
    result = run_setup()
    print("Setup Result:", result)
