# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""S3 sync check and upload orchestration.

DCC-agnostic.  Accepts pre-configured Deadline Cloud credentials and
file paths; knows nothing about Maya, Nuke, etc.

Typical usage::

    manager = S3SyncManager(farm_id, queue_id, s3_settings, queue_session)
    plan = manager.prepare_sync(file_paths)     # hash + S3 HEAD checks
    result = manager.upload_files(plan)          # upload missing files
"""

import logging
from pathlib import Path
from typing import Callable, Optional

from deadline.client.config.config_file import get_cache_directory
from deadline.job_attachments.models import JobAttachmentS3Settings
from deadline.job_attachments.upload import S3AssetManager, S3AssetUploader

from .models import (
    ProgressInfo,
    SyncFileEntry,
    SyncPlan,
    UploadResult,
)

logger = logging.getLogger(__name__)


class S3SyncManager:
    """Orchestrates file hashing, S3 status checks, and uploads.

    Each instance is bound to a specific farm/queue/session
    combination.  Create a new instance when the user selects a
    different queue.
    """

    def __init__(
        self,
        farm_id: str,
        queue_id: str,
        s3_settings: JobAttachmentS3Settings,
        queue_session,
    ):
        self._farm_id = farm_id
        self._queue_id = queue_id
        self._s3_settings = s3_settings
        self._queue_session = queue_session

    # -- Sync check ------------------------------------------------------

    def prepare_sync(self, file_paths: list[Path]) -> SyncPlan:
        """Hash files (XXH128), check S3 existence, return a plan.

        The returned :class:`SyncPlan` retains the internal manifests
        so that :meth:`upload_files` can proceed without re-hashing.

        Args:
            file_paths: Absolute paths to check.

        Returns:
            A :class:`SyncPlan` with display data and internal state.
        """
        s3_bucket = self._s3_settings.s3BucketName
        root_prefix = self._s3_settings.rootPrefix

        # Hash files and create local manifests (in memory only)
        logger.info("Hashing %d files...", len(file_paths))
        asset_manager = S3AssetManager(
            farm_id=self._farm_id,
            queue_id=self._queue_id,
            job_attachment_settings=self._s3_settings,
            session=self._queue_session,
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

        # Collect all hashed file entries from manifests
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

        # Check S3 existence per hash
        uploader = S3AssetUploader(
            session=self._queue_session,
            s3_max_pool_connections=50,
            small_file_threshold_multiplier=20,
        )
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

            entry = SyncFileEntry(
                path=file_path, size=file_size, hash=file_hash
            )
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

        return SyncPlan(
            needs_upload=needs_upload,
            already_synced=already_synced,
            total_files=len(hashed_files),
            total_size_bytes=total_size,
            upload_size_bytes=upload_size,
            _manifests=list(manifests),
            _s3_bucket=s3_bucket,
            _root_prefix=root_prefix,
            _cache_directory=cache_directory,
        )

    # -- Upload ----------------------------------------------------------

    def upload_files(
        self,
        plan: SyncPlan,
        on_progress: Optional[Callable[[ProgressInfo], bool]] = None,
    ) -> UploadResult:
        """Upload files from a prepared :class:`SyncPlan`.

        Calls ``S3AssetManager.upload_assets()`` with the manifests
        retained by :meth:`prepare_sync`.

        Args:
            plan: A :class:`SyncPlan` from :meth:`prepare_sync`.
            on_progress: Optional callback receiving
                :class:`ProgressInfo` snapshots.  Return *False* to
                cancel the upload (the SDK raises
                ``AssetSyncCancelledError``).

        Returns:
            An :class:`UploadResult` with summary statistics.
        """
        if not plan._manifests:
            logger.info("Nothing to upload — all files already synced.")
            return UploadResult(
                uploaded_files=0,
                uploaded_bytes=0,
                skipped_files=plan.total_files,
                skipped_bytes=plan.total_size_bytes,
                total_time=0.0,
                transfer_rate=0.0,
            )

        logger.info(
            "Uploading %d file(s) (%s bytes)...",
            len(plan.needs_upload),
            f"{plan.upload_size_bytes:,}",
        )

        # Wrap the caller's progress callback into the SDK's expected
        # signature: Callable[[ProgressReportMetadata], bool].
        sdk_callback = None
        if on_progress is not None:

            def sdk_callback(metadata):
                info = ProgressInfo(
                    progress=metadata.progress,
                    message=metadata.progressMessage,
                    processed_files=metadata.processedFiles,
                    transfer_rate=metadata.transferRate,
                )
                return on_progress(info)

        asset_manager = S3AssetManager(
            farm_id=self._farm_id,
            queue_id=self._queue_id,
            job_attachment_settings=self._s3_settings,
            session=self._queue_session,
        )

        (stats, _attachments) = asset_manager.upload_assets(
            plan._manifests,
            on_uploading_assets=sdk_callback,
            s3_check_cache_dir=plan._cache_directory,
        )

        logger.info(
            "Upload complete: %d file(s), %s bytes in %.1fs (%.1f MB/s)",
            stats.processed_files,
            f"{stats.processed_bytes:,}",
            stats.total_time,
            stats.transfer_rate / (1024 * 1024) if stats.transfer_rate else 0,
        )

        return UploadResult(
            uploaded_files=stats.processed_files,
            uploaded_bytes=stats.processed_bytes,
            skipped_files=stats.skipped_files,
            skipped_bytes=stats.skipped_bytes,
            total_time=stats.total_time,
            transfer_rate=stats.transfer_rate,
        )
