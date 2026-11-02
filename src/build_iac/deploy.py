#!/usr/bin/env python3
"""LuminaLab Swarm - One-Click Automated AWS Infrastructure Provisioner (IaC).

Deploys CloudFormation template for S3, DynamoDB, and IAM policies,
guaranteeing safe isolation from existing resources and auto-syncing outputs with .env.
"""

import argparse
import datetime
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

TEMPLATE_PATH = Path(__file__).resolve().parent / "template.yaml"
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = ROOT_DIR / ".env"
DEFAULT_STACK_NAME = "LuminaLab-Swarm-Stack"


def print_banner() -> None:
    """Print architectural header banner."""
    print("╔═══════════════════════════════════════════════════════════════════════════╗")
    print("║   LuminaLab Swarm — One-Click Enterprise AWS Infrastructure (IaC)        ║")
    print("║   Serverless S3 Vault • DynamoDB Ledger • Least-Privilege IAM Policies    ║")
    print("╚═══════════════════════════════════════════════════════════════════════════╝")


def get_boto_session(region_name: str | None = None) -> Any:
    """Instantiate authenticated boto3 session with graceful error handling."""
    try:
        import boto3
        return boto3.Session(region_name=region_name)
    except ImportError:
        print("\n[ERROR] 'boto3' is required to execute AWS deployment.")
        print("Install dependencies with: pip install boto3 botocore\n")
        sys.exit(1)


def verify_aws_identity(session: Any) -> dict[str, str]:
    """Verify active AWS IAM credentials via STS."""
    try:
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        account_id = identity.get("Account", "Unknown")
        arn = identity.get("Arn", "Unknown")
        user_id = identity.get("UserId", "Unknown")

        print(f"\n[Identity Verified] AWS Account: {account_id}")
        print(f"[Caller ARN]        {arn}")
        print(f"[Region]            {session.region_name or 'us-east-1'}")

        return {
            "account_id": account_id,
            "arn": arn,
            "user_id": user_id,
        }
    except Exception as exc:
        print("\n[ERROR] Unable to authenticate with AWS STS.")
        print(f"Details: {exc}")
        print("\nPlease ensure your AWS IAM credentials are set via:")
        print("  1. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION")
        print("  2. AWS CLI profile: aws configure\n")
        sys.exit(1)


def print_isolation_guarantee() -> None:
    """Print clear safety and non-interference reassurance for enterprise clients."""
    print("\n" + "─" * 75)
    print(" [Safe Isolation Guarantee]")
    print(" This deployment uses a dedicated CloudFormation stack namespace.")
    print(" It provisions NEW, isolated serverless resources.")
    print(" It will NOT alter, touch, or conflict with any existing S3 buckets")
    print(" or DynamoDB tables in your AWS account.")
    print("─" * 75 + "\n")


def sync_env_file(env_file_path: Path, outputs: dict[str, str], auto_approve: bool = False) -> None:
    """Update or append deployed AWS resources directly into the project .env file."""
    if not env_file_path.exists():
        # Create empty file if not exists
        env_file_path.touch()

    # Backup existing .env file
    backup_path = env_file_path.with_suffix(f".backup.{int(time.time())}")
    shutil.copy2(env_file_path, backup_path)
    print(f"[Backup Created] Saved existing .env to: {backup_path.name}")

    existing_lines = env_file_path.read_text(encoding="utf-8").splitlines()
    updates = {
        "AWS_REGION": outputs.get("AwsRegion", "us-east-1"),
        "S3_BUCKET_NAME": outputs.get("S3BucketName", ""),
        "DYNAMO_TABLE_NAME": outputs.get("DynamoTableName", ""),
        "LUMINA_MOCK_MODE": "false",
    }

    new_lines = []
    applied_keys = set()

    for line in existing_lines:
        line_stripped = line.strip()
        if "=" in line_stripped and not line_stripped.startswith("#"):
            k = line_stripped.split("=", 1)[0].strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}")
                applied_keys.add(k)
                continue
        new_lines.append(line)

    for k, v in updates.items():
        if k not in applied_keys:
            new_lines.append(f"{k}={v}")

    env_file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"[Sync Complete] Updated {env_file_path.name} with live cloud parameters:")
    for k, v in updates.items():
        print(f"  ✓ {k}={v}")


def monitor_stack_events(cf_client: Any, stack_name: str, start_time: datetime.datetime, is_delete: bool = False) -> None:
    """Stream live CloudFormation deployment events to stdout."""
    seen_events: set[str] = set()
    terminal_statuses = {"CREATE_COMPLETE", "UPDATE_COMPLETE", "ROLLBACK_COMPLETE", "CREATE_FAILED", "UPDATE_FAILED", "DELETE_COMPLETE", "DELETE_FAILED"}

    while True:
        try:
            resp = cf_client.describe_stack_events(StackName=stack_name)
            events = resp.get("StackEvents", [])
            for ev in reversed(events):
                ev_id = ev.get("EventId", "")
                ev_time = ev.get("Timestamp", start_time)
                if ev_id not in seen_events and ev_time >= start_time:
                    seen_events.add(ev_id)
                    logical_id = ev.get("LogicalResourceId", "")
                    res_type = ev.get("ResourceType", "")
                    status = ev.get("ResourceStatus", "")
                    reason = ev.get("ResourceStatusReason", "")
                    status_line = f"  • [{logical_id}] ({res_type}) -> {status}"
                    if reason and "FAILED" in status:
                        status_line += f" : {reason}"
                    print(status_line)
        except Exception as exc:
            if is_delete or "does not exist" in str(exc).lower():
                break

        # Check overall stack status
        try:
            stacks = cf_client.describe_stacks(StackName=stack_name).get("Stacks", [])
            if stacks:
                current_status = stacks[0].get("StackStatus", "")
                if current_status in terminal_statuses:
                    break
        except Exception as exc:
            if is_delete or "does not exist" in str(exc).lower():
                break

        time.sleep(3)


def deploy_stack(stack_name: str, region: str, env_file: Path, auto_approve: bool = False, dry_run: bool = False) -> None:
    """Execute CloudFormation stack deployment."""
    session = get_boto_session(region_name=region)
    verify_aws_identity(session)
    print_isolation_guarantee()

    if not TEMPLATE_PATH.exists():
        print(f"[ERROR] CloudFormation template not found at: {TEMPLATE_PATH}")
        sys.exit(1)

    template_body = TEMPLATE_PATH.read_text(encoding="utf-8")
    cf_client = session.client("cloudformation")

    # Validate template with AWS
    print("[Validation] Validating CloudFormation template against AWS API...")
    try:
        cf_client.validate_template(TemplateBody=template_body)
        print("  ✓ Template is syntactically valid and approved by AWS.")
    except Exception as exc:
        print(f"[ERROR] Template validation failed: {exc}")
        sys.exit(1)

    if dry_run:
        print("\n[Dry-Run Mode] Validation passed. Skipping resource creation.")
        return

    # Check if stack already exists
    stack_exists = False
    try:
        existing = cf_client.describe_stacks(StackName=stack_name).get("Stacks", [])
        if existing and existing[0].get("StackStatus") != "DELETE_COMPLETE":
            stack_exists = True
    except Exception:
        stack_exists = False

    action_label = "UPDATE" if stack_exists else "CREATE"
    print(f"\n[Execution Plan] Action: {action_label} | Stack: {stack_name} | Region: {region}")
    print("Resources to provision:")
    print("  1. AWS::S3::Bucket        -> LuminaLabVaultBucket (with Web CORS)")
    print("  2. AWS::DynamoDB::Table   -> LuminaLabImpactTable (On-Demand PAY_PER_REQUEST)")
    print("  3. AWS::IAM::ManagedPolicy-> LuminaLabSwarmPolicy (Least-Privilege)")

    if not auto_approve:
        try:
            confirm = input("\nProceed with AWS deployment? (Y/n): ").strip().lower()
            if confirm and confirm not in ("y", "yes"):
                print("[Aborted] Deployment cancelled by user.")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\n[Aborted] Deployment cancelled.")
            sys.exit(0)

    start_time = datetime.datetime.now(datetime.timezone.utc)
    t0 = time.time()
    print(f"\n[Deploying] Initiating CloudFormation {action_label}...")

    try:
        if not stack_exists:
            cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                Parameters=[
                    {"ParameterKey": "EnvironmentName", "ParameterValue": "prod"},
                    {"ParameterKey": "BillingMode", "ParameterValue": "PAY_PER_REQUEST"},
                ],
            )
        else:
            cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
                Parameters=[
                    {"ParameterKey": "EnvironmentName", "ParameterValue": "prod"},
                    {"ParameterKey": "BillingMode", "ParameterValue": "PAY_PER_REQUEST"},
                ],
            )
    except Exception as exc:
        if "No updates are to be performed" in str(exc):
            print("[Up-to-Date] Stack resources are already in the desired state.")
        else:
            print(f"[ERROR] Failed to initiate deployment: {exc}")
            sys.exit(1)

    print("[Progress] Streaming live deployment events:")
    monitor_stack_events(cf_client, stack_name, start_time)

    # Fetch final outputs
    stacks = cf_client.describe_stacks(StackName=stack_name).get("Stacks", [])
    if not stacks:
        print("[ERROR] Stack could not be retrieved.")
        sys.exit(1)

    final_status = stacks[0].get("StackStatus", "")
    elapsed = round(time.time() - t0, 1)

    if final_status in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
        print(f"\n[SUCCESS] Cloud infrastructure deployed successfully in {elapsed}s!")
        outputs = {
            item["OutputKey"]: item["OutputValue"]
            for item in stacks[0].get("Outputs", [])
        }
        print("\nDeployed Cloud Endpoints:")
        print(f"  • S3 Vault Bucket : {outputs.get('S3BucketName')}")
        print(f"  • DynamoDB Ledger : {outputs.get('DynamoTableName')}")
        print(f"  • IAM Policy ARN  : {outputs.get('IamPolicyArn')}")
        print(f"  • AWS Region      : {outputs.get('AwsRegion')}")

        sync_env_file(env_file, outputs, auto_approve=auto_approve)
        print("\n[Production Ready] LuminaLab Swarm is now configured to use live AWS services.")
    else:
        print(f"\n[FAILED] Stack deployment ended with status: {final_status}")
        sys.exit(1)


def destroy_stack(stack_name: str, region: str, auto_approve: bool = False) -> None:
    """Tear down CloudFormation stack cleanly upon request."""
    session = get_boto_session(region_name=region)
    verify_aws_identity(session)
    cf_client = session.client("cloudformation")

    # Check if stack exists before deleting
    try:
        stacks = cf_client.describe_stacks(StackName=stack_name).get("Stacks", [])
        if not stacks or stacks[0].get("StackStatus") == "DELETE_COMPLETE":
            print(f"[Notice] CloudFormation stack '{stack_name}' does not exist or is already deleted.")
            return
    except Exception:
        print(f"[Notice] CloudFormation stack '{stack_name}' does not exist or is already deleted.")
        return

    print(f"\n[Teardown Warning] You are about to DESTROY CloudFormation stack: {stack_name}")
    print("This will delete the LuminaLab S3 bucket, DynamoDB table, and IAM policy.")

    if not auto_approve:
        try:
            confirm = input("\nAre you ABSOLUTELY sure you want to delete all resources? (yes/N): ").strip()
            if confirm != "yes":
                print("[Aborted] Destruction cancelled.")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\n[Aborted] Destruction cancelled.")
            sys.exit(0)

    start_time = datetime.datetime.now(datetime.timezone.utc)
    t0 = time.time()
    print(f"\n[Destroying] Initiating stack deletion for '{stack_name}'...")
    try:
        cf_client.delete_stack(StackName=stack_name)
    except Exception as exc:
        print(f"[ERROR] Failed to initiate deletion: {exc}")
        sys.exit(1)

    monitor_stack_events(cf_client, stack_name, start_time, is_delete=True)
    print(f"\n[SUCCESS] Cloud infrastructure deleted cleanly in {round(time.time() - t0, 1)}s.")


def main() -> None:
    """CLI Entry point."""
    print_banner()

    parser = argparse.ArgumentParser(
        description="LuminaLab Swarm - Automated AWS IaC Provisioner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--stack-name",
        default=os.getenv("CFN_STACK_NAME", DEFAULT_STACK_NAME),
        help="CloudFormation stack name",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_REGION", "us-east-1"),
        help="AWS deployment region",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="Path to project .env file to synchronize",
    )
    parser.add_argument(
        "-y", "--yes",
        dest="auto_approve",
        action="store_true",
        help="Automatically approve prompts without interactive confirmation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CloudFormation template without provisioning resources",
    )
    parser.add_argument(
        "--destroy",
        action="store_true",
        help="Tear down and delete all provisioned CloudFormation resources",
    )

    args = parser.parse_args()

    if args.destroy:
        destroy_stack(stack_name=args.stack_name, region=args.region, auto_approve=args.auto_approve)
    else:
        deploy_stack(
            stack_name=args.stack_name,
            region=args.region,
            env_file=args.env_file,
            auto_approve=args.auto_approve,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
