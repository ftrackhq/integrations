# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""AWS Deadline Cloud wrapper for farm/queue discovery and S3 sync checks.

Requires Deadline Cloud Monitor to be installed and configured on the
artist's machine.  The SDK's ``get_boto3_session()`` reads credentials
from ``~/.deadline/config`` and the AWS credential chain.
"""

import logging
from pathlib import Path
from typing import Optional

import boto3

from deadline.client.api import get_boto3_session
from deadline.client import api
from deadline.job_attachments.models import JobAttachmentS3Settings
from deadline.job_attachments.upload import S3AssetManager, S3AssetUploader
from deadline.client.config.config_file import get_cache_directory, get_setting

logger = logging.getLogger(__name__)


class DeadlineWrapper:
    """AWS Deadline Cloud operations for farm/queue discovery and S3 sync
    status checks.

    All boto3 clients are lazy-initialised on first access so that
    creating the wrapper instance is cheap and fast.
    """

    def __init__(self, profile: Optional[str] = None):
        self._profile = profile
        self._aws_session = None
        self._deadline = None

    # -- Lazy-init properties -----------------------------------------

    @property
    def aws_session(self) -> boto3.Session:
        """Return the default boto3 session (Deadline Cloud Monitor creds)."""
        if self._aws_session is None:
            self._aws_session = get_boto3_session()
        return self._aws_session

    @property
    def deadline(self):
        """Return the Deadline Cloud service client."""
        if self._deadline is None:
            self._deadline = self.aws_session.client("deadline")
        return self._deadline

    # -- Configuration ------------------------------------------------

    def get_configured_defaults(self) -> dict:
        """Return configured defaults from ``~/.deadline/config``.

        Returns:
            dict with ``farm_id`` and ``queue_id`` keys (values may be
            *None* if not configured).
        """
        farm_id = get_setting("defaults.farm_id") or None
        queue_id = get_setting("defaults.queue_id") or None
        return {"farm_id": farm_id, "queue_id": queue_id}

    # -- Farm / queue discovery ---------------------------------------

    def list_farms(self) -> list[dict]:
        """Return all available farms.

        Each dict contains at least ``farmId`` and ``displayName``.
        """
        response = api.list_farms()
        return response.get("farms", [])

    def list_queues(self, farm_id: str) -> list[dict]:
        """Return all queues for *farm_id*.

        Each dict contains at least ``queueId`` and ``displayName``.
        """
        response = api.list_queues(farmId=farm_id)
        return response.get("queues", [])

    def get_queue_settings(
        self, farm_id: str, queue_id: str
    ) -> tuple[dict, JobAttachmentS3Settings]:
        """Return ``(queue_dict, s3_settings)`` for a queue."""
        queue = self.deadline.get_queue(farmId=farm_id, queueId=queue_id)
        s3_settings = JobAttachmentS3Settings(**queue["jobAttachmentSettings"])
        return queue, s3_settings

    def get_queue_session(
        self,
        farm_id: str,
        queue_id: str,
        queue_name: Optional[str] = None,
    ) -> boto3.Session:
        """Return a queue-scoped boto3 session for S3 access."""
        return api.get_queue_user_boto3_session(
            deadline=self.deadline,
            config=None,
            farm_id=farm_id,
            queue_id=queue_id,
            queue_display_name=queue_name,
        )

    # -- Sync status check --------------------------------------------

    def check_sync_status(
        self,
        file_paths: list[Path],
        farm_id: str,
        queue_id: str,
    ) -> dict:
        """Hash local files and check which are already on S3.

        This does **not** upload anything.  It hashes every file in
        *file_paths* (XXH128, with local cache) and issues an S3 HEAD
        request per hash to determine whether the content already exists
        in the queue's content-addressable store.

        Args:
            file_paths: Absolute paths to check.
            farm_id: Deadline Cloud farm ID.
            queue_id: Deadline Cloud queue ID.

        Returns:
            dict with keys::

                needs_upload    – list of {path, size, hash}
                already_synced  – list of {path, size, hash}
                total_files     – int
                total_size_bytes – int
                upload_size_bytes – int (sum of sizes not yet on S3)
        """
        # 1. Queue settings (bucket + rootPrefix)
        queue, s3_settings = self.get_queue_settings(farm_id, queue_id)
        s3_bucket = s3_settings.s3BucketName
        root_prefix = s3_settings.rootPrefix

        # 2. Queue-scoped session for S3 access
        queue_session = self.get_queue_session(
            farm_id, queue_id, queue.get("displayName")
        )

        # 3. Hash files and create local manifests (in memory only)
        logger.info("Hashing %d files...", len(file_paths))
        asset_manager = S3AssetManager(
            farm_id=farm_id,
            queue_id=queue_id,
            job_attachment_settings=s3_settings,
            session=queue_session,
        )

        upload_group = asset_manager.prepare_paths_for_upload(
            file_paths,
            [],  # no output directories
            [],  # no referenced paths
        )

        cache_directory = get_cache_directory()
        (_, manifests) = asset_manager.hash_assets_and_create_manifest(
            upload_group.asset_groups,
            upload_group.total_input_files,
            upload_group.total_input_bytes,
            cache_directory,
        )

        # 4. Collect all hashed file entries from manifests
        hashed_files = []
        for manifest_root in manifests:
            if not manifest_root.asset_manifest:
                continue
            for path_obj in manifest_root.asset_manifest.paths:
                hashed_files.append(path_obj)

        logger.info(
            "Hashing complete: %d file(s). Checking S3 existence...",
            len(hashed_files),
        )

        # 5. Check S3 existence per hash
        uploader = S3AssetUploader(session=queue_session)
        needs_upload = []
        already_synced = []
        upload_size = 0
        total_size = 0

        for path_obj in hashed_files:
            file_size = path_obj.size if hasattr(path_obj, "size") else 0
            file_hash = path_obj.hash if hasattr(path_obj, "hash") else ""
            file_path = str(path_obj.path) if hasattr(path_obj, "path") else ""
            total_size += file_size

            s3_key = f"{root_prefix}/Data/{file_hash}.xxh128"

            try:
                on_s3 = uploader.file_already_uploaded(s3_bucket, s3_key)
            except Exception:
                logger.warning(
                    "S3 check failed for %s — assuming needs upload",
                    file_hash,
                    exc_info=True,
                )
                on_s3 = False

            entry = {"path": file_path, "size": file_size, "hash": file_hash}
            if on_s3:
                already_synced.append(entry)
            else:
                needs_upload.append(entry)
                upload_size += file_size

        logger.info(
            "Sync check complete: %d need upload (%s bytes), "
            "%d already synced",
            len(needs_upload),
            f"{upload_size:,}",
            len(already_synced),
        )

        return {
            "needs_upload": needs_upload,
            "already_synced": already_synced,
            "total_files": len(hashed_files),
            "total_size_bytes": total_size,
            "upload_size_bytes": upload_size,
        }
