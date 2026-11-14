"""Credential lookup rules (credentials.py), with a fake boto3: no AWS or Space-Track access."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sattrack_ingest import credentials as cr  # noqa: E402

ARN = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:sattrack/spacetrack-AbCdEf"
ENV_VARS = ["GITHUB_ACTIONS", "SATTRACK_CREDENTIAL_SOURCE", "SATTRACK_SPACETRACK_SECRET_ID", "SPACETRACK_USER", "SPACETRACK_PASS"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for v in ENV_VARS:
        monkeypatch.delenv(v, raising=False)


def fake_boto3(monkeypatch, payload=None, error=None):
    calls = []

    class Client:
        def get_secret_value(self, SecretId):
            calls.append(("get", SecretId))
            if error:
                raise error
            return {"SecretString": payload}

    def client(service, region_name=None):
        calls.append(("client", service, region_name))
        return Client()

    monkeypatch.setitem(sys.modules, "boto3", types.SimpleNamespace(client=client))
    return calls


def test_env_vars_used_locally(monkeypatch):
    monkeypatch.setenv("SPACETRACK_USER", "u")
    monkeypatch.setenv("SPACETRACK_PASS", "p")
    assert cr.resolve_spacetrack_credentials() == ("u", "p")


def test_ci_ignores_env_vars_and_uses_secret(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("SPACETRACK_USER", "stray")
    monkeypatch.setenv("SPACETRACK_PASS", "stray")
    monkeypatch.setenv("SATTRACK_SPACETRACK_SECRET_ID", ARN)
    calls = fake_boto3(monkeypatch, json.dumps({"username": "su", "password": "sp"}))
    assert cr.resolve_spacetrack_credentials() == ("su", "sp")
    assert ("client", "secretsmanager", "eu-west-1") in calls


def test_ci_without_secret_id_fails_closed(monkeypatch):
    monkeypatch.setenv("SATTRACK_CREDENTIAL_SOURCE", "secretsmanager")
    monkeypatch.setenv("SPACETRACK_USER", "u")
    monkeypatch.setenv("SPACETRACK_PASS", "p")
    with pytest.raises(cr.CredentialsError, match="SATTRACK_SPACETRACK_SECRET_ID is not set"):
        cr.resolve_spacetrack_credentials()


def test_plain_secret_name_uses_default_region(monkeypatch):
    monkeypatch.setenv("SATTRACK_SPACETRACK_SECRET_ID", "sattrack/spacetrack")
    calls = fake_boto3(monkeypatch, json.dumps({"username": "su", "password": "sp"}))
    cr.resolve_spacetrack_credentials()
    assert ("client", "secretsmanager", None) in calls


@pytest.mark.parametrize("arn, region", [
    (ARN, "eu-west-1"),
    ("sattrack/spacetrack", None),
    ("arn:aws:s3:::bucket", None),
])
def test_region_from_arn(arn, region):
    assert cr.region_from_arn(arn) == region


@pytest.mark.parametrize("payload", ['{"username": "su", "password": "SECRETVALUE"', '["SECRETVALUE"]',
                                     '{"username": "su", "pass": "SECRETVALUE"}'])
def test_bad_payload_never_echoes_values(monkeypatch, payload):
    monkeypatch.setenv("SATTRACK_SPACETRACK_SECRET_ID", ARN)
    fake_boto3(monkeypatch, payload)
    with pytest.raises(cr.CredentialsError) as ei:
        cr.resolve_spacetrack_credentials()
    assert "SECRETVALUE" not in str(ei.value)
    # no chained exception that a traceback would print (it could carry the payload)
    assert ei.value.__cause__ is None
    assert ei.value.__context__ is None or ei.value.__suppress_context__


def test_aws_error_text_not_echoed(monkeypatch):
    monkeypatch.setenv("SATTRACK_SPACETRACK_SECRET_ID", ARN)
    fake_boto3(monkeypatch, error=RuntimeError(f"AccessDenied for {ARN}"))
    with pytest.raises(cr.CredentialsError) as ei:
        cr.resolve_spacetrack_credentials()
    assert ARN not in str(ei.value) and "RuntimeError" in str(ei.value)
