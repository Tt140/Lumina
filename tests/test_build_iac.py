"""Unit tests for LuminaLab IaC template and deployment module."""

import subprocess
import sys
from pathlib import Path

IAC_DIR = Path(__file__).resolve().parent.parent / "src" / "build_iac"


def test_iac_files_exist():
    """Verify all required IaC files exist in src/build_iac/."""
    assert (IAC_DIR / "template.yaml").exists()
    assert (IAC_DIR / "deploy.py").exists()
    assert (IAC_DIR / "README.md").exists()
    assert (IAC_DIR / "__init__.py").exists()


def test_template_yaml_structure():
    """Verify CloudFormation template contains required resources and outputs."""
    template_text = (IAC_DIR / "template.yaml").read_text(encoding="utf-8")
    assert "AWSTemplateFormatVersion" in template_text
    assert "LuminaLabVaultBucket" in template_text
    assert "LuminaLabImpactTable" in template_text
    assert "LuminaLabSwarmPolicy" in template_text
    assert "S3BucketName" in template_text
    assert "DynamoTableName" in template_text
    assert "PAY_PER_REQUEST" in template_text


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


def test_readme_contains_enterprise_metrics():
    """Verify README contains results-driven metrics and isolation guarantee."""
    readme_text = (IAC_DIR / "README.md").read_text(encoding="utf-8")
    assert "Safe Isolation Guarantee" in readme_text
    assert "Time to Cloud" in readme_text
    assert "PAY_PER_REQUEST" in readme_text
