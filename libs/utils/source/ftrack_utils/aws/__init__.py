# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""
AWS Deadline Cloud utilities for S3 sync operations.

Provides DCC-agnostic functions for Deadline Cloud configuration,
farm/queue discovery, and S3 content-addressable storage sync
(hash, check, upload).  DCC-specific code (scene tracing, Qt
dialogs) lives in the respective integration projects.

Requires the ``[aws]`` extra: ``pip install ftrack-utils[aws]``
which pulls in ``deadline`` and ``boto3``.
"""

from .models import (
    DownloadResult,
    ProgressInfo,
    SyncFileEntry,
    SyncPlan,
    UploadResult,
)
from .s3_sync import S3SyncManager
from .deadline import (
    get_configured_defaults,
    get_deadline_boto3_session,
    get_queue_session,
    get_queue_settings,
    is_credential_error,
    is_network_error,
    list_farms,
    list_queues,
)

__all__ = [
    "DownloadResult",
    "ProgressInfo",
    "S3SyncManager",
    "SyncFileEntry",
    "SyncPlan",
    "UploadResult",
    "get_configured_defaults",
    "get_deadline_boto3_session",
    "is_credential_error",
    "is_network_error",
    "get_queue_session",
    "get_queue_settings",
    "list_farms",
    "list_queues",
]
