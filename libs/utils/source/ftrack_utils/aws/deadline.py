# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Deadline Cloud configuration, discovery, and session management.

Stateless functions that wrap the deadline SDK for farm/queue
discovery and boto3 session creation.  Requires Deadline Cloud
Monitor to be installed and configured on the artist's machine.
"""

import logging
from typing import Optional

import boto3
from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    CredentialRetrievalError,
    EndpointConnectionError,
    NoCredentialsError,
    PartialCredentialsError,
)

from deadline.client.api import get_boto3_session
from deadline.client import api
from deadline.client.config.config_file import get_setting
from deadline.job_attachments.models import JobAttachmentS3Settings

logger = logging.getLogger(__name__)


def is_credential_error(exc: Exception) -> bool:
    """Return True if *exc* indicates invalid or missing AWS credentials."""
    if isinstance(
        exc,
        (
            NoCredentialsError,
            PartialCredentialsError,
            CredentialRetrievalError,
        ),
    ):
        return True
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        if code in (
            "ExpiredTokenException",
            "UnrecognizedClientException",
            "InvalidIdentityToken",
            "AccessDeniedException",
        ):
            return True
    return False


def is_network_error(exc: Exception) -> bool:
    """Return True if *exc* indicates a network connectivity problem."""
    return isinstance(exc, (EndpointConnectionError, ConnectTimeoutError))


def get_deadline_boto3_session() -> boto3.Session:
    """Return the default boto3 session from Deadline Cloud Monitor.

    Reads credentials from ``~/.deadline/config`` and the AWS
    credential chain.
    """
    return get_boto3_session()


def get_configured_defaults() -> dict:
    """Read farm/queue defaults from ``~/.deadline/config``.

    Returns:
        dict with ``farm_id`` and ``queue_id`` keys (values may be
        *None* if not configured).
    """
    farm_id = get_setting("defaults.farm_id") or None
    queue_id = get_setting("defaults.queue_id") or None
    return {"farm_id": farm_id, "queue_id": queue_id}


def list_farms() -> list[dict]:
    """Return all available Deadline Cloud farms.

    Each dict contains at least ``farmId`` and ``displayName``.
    """
    response = api.list_farms()
    return response.get("farms", [])


def list_queues(farm_id: str) -> list[dict]:
    """Return all queues for *farm_id*.

    Each dict contains at least ``queueId`` and ``displayName``.
    """
    response = api.list_queues(farmId=farm_id)
    return response.get("queues", [])


def get_queue_settings(
    deadline_client, farm_id: str, queue_id: str
) -> tuple[dict, JobAttachmentS3Settings]:
    """Return ``(queue_dict, s3_settings)`` for a queue.

    Args:
        deadline_client: A ``deadline`` service client
            (``boto3_session.client("deadline")``).
        farm_id: Deadline Cloud farm ID.
        queue_id: Deadline Cloud queue ID.
    """
    queue = deadline_client.get_queue(farmId=farm_id, queueId=queue_id)
    s3_settings = JobAttachmentS3Settings(**queue["jobAttachmentSettings"])
    return queue, s3_settings


def get_queue_session(
    deadline_client,
    config,
    farm_id: str,
    queue_id: str,
    queue_name: Optional[str] = None,
) -> boto3.Session:
    """Return a queue-scoped boto3 session for S3 access.

    Uses temporary credentials with a queue-specific IAM role.

    Args:
        deadline_client: A ``deadline`` service client.
        config: Deadline config object (or *None* for default).
        farm_id: Deadline Cloud farm ID.
        queue_id: Deadline Cloud queue ID.
        queue_name: Optional display name for logging.
    """
    return api.get_queue_user_boto3_session(
        deadline=deadline_client,
        config=config,
        farm_id=farm_id,
        queue_id=queue_id,
        queue_display_name=queue_name,
    )
