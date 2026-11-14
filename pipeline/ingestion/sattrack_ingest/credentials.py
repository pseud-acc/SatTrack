"""Space-Track credential lookup (credentials plan, 2026-10-11; CI rules 2026-11-09).

Order: SPACETRACK_USER / SPACETRACK_PASS env vars (e.g. sourced from a local, gitignored .env.sh),
then an AWS Secrets Manager secret named by SATTRACK_SPACETRACK_SECRET_ID (default AWS credential
chain; boto3 imported lazily), otherwise a clear error.

In CI (GITHUB_ACTIONS=true) or with SATTRACK_CREDENTIAL_SOURCE=secretsmanager, only Secrets Manager is
used: env-var credentials are ignored, so a stray SPACETRACK_PASS in a runner can never be picked up.
The region comes from the secret's ARN when the id is an ARN, else from the AWS environment.

Values are never logged, and no error message carries a value, the secret's payload or AWS error text.
"""
from __future__ import annotations

import json
import os

SECRETS_MANAGER = "secretsmanager"


class CredentialsError(RuntimeError):
    pass


def secrets_manager_required() -> bool:
    return (os.environ.get("GITHUB_ACTIONS") == "true"
            or os.environ.get("SATTRACK_CREDENTIAL_SOURCE", "").lower() == SECRETS_MANAGER)


def region_from_arn(secret_id: str) -> str | None:
    """arn:aws:secretsmanager:<region>:<account>:secret:<name> -> <region>; None for a plain name."""
    parts = secret_id.split(":")
    if len(parts) >= 7 and parts[0] == "arn" and parts[2] == SECRETS_MANAGER and parts[3]:
        return parts[3]
    return None


def _from_secrets_manager(secret_id: str) -> tuple[str, str]:
    try:
        import boto3  # lazy: only needed for the Secrets Manager path
    except ImportError:  # pragma: no cover
        raise CredentialsError("SATTRACK_SPACETRACK_SECRET_ID is set but boto3 is not installed") from None
    region = region_from_arn(secret_id)
    try:
        client = boto3.client(SECRETS_MANAGER, region_name=region) if region else boto3.client(SECRETS_MANAGER)
        payload = client.get_secret_value(SecretId=secret_id)["SecretString"]
    except Exception as exc:  # noqa: BLE001 - only the type name leaves this function
        raise CredentialsError(f"Could not read the Space-Track secret from Secrets Manager ({type(exc).__name__})") from None
    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        raise CredentialsError("The Space-Track secret is not a JSON object") from None
    if not isinstance(data, dict):
        raise CredentialsError("The Space-Track secret is not a JSON object")
    user, password = data.get("username"), data.get("password")
    if isinstance(user, str) and isinstance(password, str) and user and password:
        return user, password
    raise CredentialsError("The Space-Track secret is missing the 'username' or 'password' key")


def resolve_spacetrack_credentials() -> tuple[str, str]:
    secret_id = os.environ.get("SATTRACK_SPACETRACK_SECRET_ID")
    if secrets_manager_required():
        if not secret_id:
            raise CredentialsError("Secrets Manager is required here (CI or SATTRACK_CREDENTIAL_SOURCE) "
                                   "but SATTRACK_SPACETRACK_SECRET_ID is not set")
        return _from_secrets_manager(secret_id)
    user, password = os.environ.get("SPACETRACK_USER"), os.environ.get("SPACETRACK_PASS")
    if user and password:
        return user, password
    if secret_id:
        return _from_secrets_manager(secret_id)
    raise CredentialsError(
        "No Space-Track credentials: set SPACETRACK_USER and SPACETRACK_PASS, "
        "or SATTRACK_SPACETRACK_SECRET_ID for AWS Secrets Manager."
    )
