"""Unit tests for LuminaLab IaC template and deployment module."""

import subprocess
import sys
from pathlib import Path
import yaml

IAC_DIR = Path(__file__).resolve().parent.parent / "src" / "build_iac"


class _CfnYamlLoader(yaml.SafeLoader):
    """YAML loader supporting CloudFormation intrinsic tags (!Ref, !Sub, !GetAtt, !Not, !Equals)."""


def _cfn_tag_constructor(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node):
    if isinstance(node, yaml.ScalarNode):
        return {f"!{tag_suffix}": loader.construct_scalar(node)}
    if isinstance(node, yaml.SequenceNode):
        return {f"!{tag_suffix}": loader.construct_sequence(node)}
    return {f"!{tag_suffix}": loader.construct_mapping(node)}


_CfnYamlLoader.add_multi_constructor("!", _cfn_tag_constructor)


def _load_template() -> dict:
    return yaml.load((IAC_DIR / "template.yaml").read_text(encoding="utf-8"), Loader=_CfnYamlLoader)


def test_iac_files_exist():
    """Verify all required IaC files exist in src/build_iac/."""
    assert (IAC_DIR / "template.yaml").exists()
    assert (IAC_DIR / "deploy.py").exists()
    assert (IAC_DIR / "README.md").exists()
    assert (IAC_DIR / "__init__.py").exists()


def test_template_yaml_structure():
    """Verify CloudFormation template contains required resources and outputs."""
    tpl = _load_template()
    resources = tpl["Resources"]
    outputs = tpl["Outputs"]

    assert "AWSTemplateFormatVersion" in tpl
    assert "LuminaLabVaultBucket" in resources
    assert "LuminaLabImpactTable" in resources
    assert "LuminaLabSwarmPolicy" in resources
    assert "S3BucketName" in outputs
    assert "DynamoTableName" in outputs
    assert "AppLogGroupName" in outputs
    assert "AlertsTopicArn" in outputs
    assert "PAY_PER_REQUEST" in tpl["Parameters"]["BillingMode"]["AllowedValues"]


def test_template_removes_dynamodb_scan_permission():
    """Verify F-05B IAM hardening: LuminaLabSwarmPolicy removes dynamodb:Scan completely."""
    tpl = _load_template()
    policy_doc = tpl["Resources"]["LuminaLabSwarmPolicy"]["Properties"]["PolicyDocument"]
    all_actions = []
    dynamo_stmt = None
    for stmt in policy_doc["Statement"]:
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        all_actions.extend(actions)
        if stmt.get("Sid") == "DynamoImpactLedgerAccess":
            dynamo_stmt = stmt

    assert "dynamodb:Scan" not in all_actions
    assert dynamo_stmt is not None
    assert set(dynamo_stmt["Action"]) == {
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
    }
    assert dynamo_stmt["Resource"] == [{"!GetAtt": "LuminaLabImpactTable.Arn"}]


def test_template_includes_cloudwatch_logs_sns_and_alarms():
    """Verify F-05C observability: LogGroup with retention, encrypted SNS topic, and DynamoDB alarms."""
    tpl = _load_template()
    resources = tpl["Resources"]

    # Optional email parameter so automated CLI deployments require zero manual inputs
    assert tpl["Parameters"]["NotificationEmail"]["Default"] == ""
    assert "HasNotificationEmail" in tpl["Conditions"]

    # CloudWatch LogGroup with explicit RetentionInDays
    log_group = resources["LuminaLabAppLogGroup"]
    assert log_group["Type"] == "AWS::Logs::LogGroup"
    assert isinstance(log_group["Properties"]["RetentionInDays"], int)
    assert log_group["Properties"]["RetentionInDays"] in (14, 30)
    assert any(t["Key"] == "Project" for t in log_group["Properties"]["Tags"])

    # Encrypted SNS Topic & optional email subscription
    sns_topic = resources["LuminaLabAlertsTopic"]
    assert sns_topic["Type"] == "AWS::SNS::Topic"
    assert "KmsMasterKeyId" in sns_topic["Properties"]
    assert resources["LuminaLabAlertsKmsKey"]["Type"] == "AWS::KMS::Key"
    assert resources["LuminaLabAlertsKmsKey"]["Properties"]["EnableKeyRotation"] is True
    assert resources["LuminaLabAlertsTopicPolicy"]["Type"] == "AWS::SNS::TopicPolicy"
    sub = resources["LuminaLabAlertsEmailSubscription"]
    assert sub["Type"] == "AWS::SNS::Subscription"
    assert sub["Condition"] == "HasNotificationEmail"

    # Real CloudWatch Alarms wired to AlertsTopic
    alarms = {
        name: res
        for name, res in resources.items()
        if res["Type"] == "AWS::CloudWatch::Alarm"
    }
    assert {
        "LuminaLabDynamoSystemErrorsAlarm",
        "LuminaLabDynamoThrottleAlarm",
        "LuminaLabDynamoUserErrorsAlarm",
        "LuminaLabDynamoFallbackAlarm",
    }.issubset(alarms.keys())

    for alarm_name, alarm in alarms.items():
        props = alarm["Properties"]
        assert props["AlarmActions"] == [{"!Ref": "LuminaLabAlertsTopic"}], alarm_name
        assert props["TreatMissingData"] == "notBreaching", alarm_name
        assert {t["Key"] for t in props["Tags"]} >= {"Project", "Environment", "ManagedBy"}, alarm_name


def test_deploy_cli_help():
    """Verify deploy.py executes --help cleanly."""
    result = subprocess.run(
        [sys.executable, str(IAC_DIR / "deploy.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "LuminaLab Swarm - Automated AWS IaC Provisioner" in result.stdout
    assert "--stack-name" in result.stdout
    assert "--destroy" in result.stdout
    assert "--alert-email" in result.stdout


def test_readme_contains_enterprise_metrics():
    """Verify README contains results-driven metrics and isolation guarantee."""
    readme_text = (IAC_DIR / "README.md").read_text(encoding="utf-8")
    assert "Safe Isolation Guarantee" in readme_text
    assert "Time to Cloud" in readme_text
    assert "PAY_PER_REQUEST" in readme_text
