"""DynamoDB helpers for user and session persistence.

All public functions are silent no-ops when DynamoDB is not configured
or when demo=True, so the app works without any AWS credentials.
"""

import os
import decimal
import logging
from datetime import datetime, timezone
from typing import Optional
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)


def is_dynamo_configured() -> bool:
    """Return True when AWS credentials are available (key or profile)."""
    return bool(
        os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE")
    )


def _get_client():
    import boto3
    region = os.getenv("AWS_REGION", "us-east-1")
    return boto3.client("dynamodb", region_name=region)


def _get_resource():
    import boto3
    region = os.getenv("AWS_REGION", "us-east-1")
    return boto3.resource("dynamodb", region_name=region)


def upsert_user(
    user_id: str,
    email: str,
    name: str,
    picture: str,
    demo: bool = False,
) -> None:
    """Upsert a user record in nova_users.

    Uses update_item so repeated logins update last_login without
    overwriting the original created_at timestamp.
    """
    if demo or not is_dynamo_configured():
        return

    table = os.getenv("DYNAMO_USERS_TABLE", "nova_users")
    now = datetime.now(timezone.utc).isoformat()

    try:
        client = _get_client()
        client.update_item(
            TableName=table,
            Key={"user_id": {"S": user_id}},
            UpdateExpression=(
                "SET email = :email, #nm = :name, picture = :picture, "
                "last_login = :now, "
                "created_at = if_not_exists(created_at, :now)"
            ),
            ExpressionAttributeNames={"#nm": "name"},
            ExpressionAttributeValues={
                ":email": {"S": email},
                ":name": {"S": name},
                ":picture": {"S": picture},
                ":now": {"S": now},
            },
        )
    except Exception:
        logger.warning("DynamoDB upsert_user failed", exc_info=True)


def save_session_record(
    user_id: str,
    session_id: str,
    role: str,
    level: str,
    language: str,
    overall_score: float,
    area_scores: dict,
    demo: bool = False,
) -> None:
    """Write a completed interview session record to nova_sessions."""
    if demo or not is_dynamo_configured():
        return

    table = os.getenv("DYNAMO_SESSIONS_TABLE", "nova_sessions")
    now = datetime.now(timezone.utc).isoformat()

    # Serialise area_scores as a DynamoDB Map
    area_scores_dynamo = {
        k: {"N": str(round(v, 2))} for k, v in (area_scores or {}).items()
    }

    try:
        client = _get_client()
        client.put_item(
            TableName=table,
            Item={
                "user_id": {"S": user_id},
                "session_id": {"S": session_id},
                "role": {"S": role},
                "level": {"S": level},
                "language": {"S": language},
                "overall_score": {"N": str(round(overall_score, 2))},
                "area_scores": {"M": area_scores_dynamo},
                "completed_at": {"S": now},
            },
        )
    except Exception:
        logger.warning("DynamoDB save_session_record failed", exc_info=True)


def _floatify(obj):
    """Recursively convert DynamoDB Decimal values to float for JSON serialization."""
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _floatify(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_floatify(i) for i in obj]
    return obj


def get_user_sessions(user_id: str, limit: int = 20) -> list:
    """Return the most recent sessions for a user from nova_sessions.

    Returns an empty list when DynamoDB is not configured.
    """
    if not is_dynamo_configured():
        return []

    table_name = os.getenv("DYNAMO_SESSIONS_TABLE", "nova_sessions")
    try:
        table = _get_resource().Table(table_name)
        resp = table.query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [_floatify(item) for item in resp.get("Items", [])]
    except Exception:
        logger.warning("DynamoDB get_user_sessions failed", exc_info=True)
        return []
