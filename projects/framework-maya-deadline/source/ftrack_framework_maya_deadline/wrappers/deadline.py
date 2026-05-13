# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""AWS Deadline Cloud wrapper for Maya integration.

Thin facade over :mod:`ftrack_utils.aws` that manages lazy-init
boto3 sessions and caches the last :class:`SyncPlan` so the dialog
can Compare then Upload without re-hashing.

Requires Deadline Cloud Monitor to be installed and configured on
the artist's machine.
"""

import logging
from pathlib import Path
from typing import Callable, Optional

from ftrack_utils.aws import (
    DownloadResult,
    S3SyncManager,
    SyncPlan,
    UploadResult,
    get_configured_defaults as _get_defaults,
    get_deadline_boto3_session,
    get_queue_session as _get_queue_session,
    get_queue_settings as _get_queue_settings,
    list_farms as _list_farms,
    list_queues as _list_queues,
)
from ftrack_utils.aws.models import ProgressInfo

logger = logging.getLogger(__name__)


class DeadlineWrapper:
    """AWS Deadline Cloud operations for the Maya sync dialog.

    Delegates configuration, discovery, and S3 sync operations to
    :mod:`ftrack_utils.aws`.  Adds lazy session management and
    plan caching for the two-step Compare → Upload flow.
    """

    def __init__(self, profile: Optional[str] = None):
        self._profile = profile
        self._aws_session = None
        self._deadline = None
        self._sync_manager: Optional[S3SyncManager] = None
        self._last_plan: Optional[SyncPlan] = None

    # -- Lazy-init properties -----------------------------------------

    @property
    def aws_session(self):
        """Return the default boto3 session (Deadline Cloud Monitor creds)."""
        if self._aws_session is None:
            self._aws_session = get_deadline_boto3_session()
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
        return _get_defaults()

    # -- Farm / queue discovery ---------------------------------------

    def list_farms(self) -> list[dict]:
        """Return all available farms.

        Each dict contains at least ``farmId`` and ``displayName``.
        """
        return _list_farms()

    def list_queues(self, farm_id: str) -> list[dict]:
        """Return all queues for *farm_id*.

        Each dict contains at least ``queueId`` and ``displayName``.
        """
        return _list_queues(farm_id)

    def get_queue_settings(self, farm_id: str, queue_id: str):
        """Return ``(queue_dict, s3_settings)`` for a queue."""
        return _get_queue_settings(self.deadline, farm_id, queue_id)

    def get_queue_session(
        self,
        farm_id: str,
        queue_id: str,
        queue_name: Optional[str] = None,
    ):
        """Return a queue-scoped boto3 session for S3 access."""
        return _get_queue_session(
            self.deadline, None, farm_id, queue_id, queue_name
        )

    # -- Sync operations ----------------------------------------------

    def _get_sync_manager(self, farm_id: str, queue_id: str) -> S3SyncManager:
        """Create an :class:`S3SyncManager` for the given queue."""
        queue, s3_settings = self.get_queue_settings(farm_id, queue_id)
        queue_session = self.get_queue_session(
            farm_id, queue_id, queue.get("displayName")
        )
        self._sync_manager = S3SyncManager(
            farm_id, queue_id, s3_settings, queue_session
        )
        return self._sync_manager

    def check_sync_status(
        self,
        file_paths: list[Path],
        farm_id: str,
        queue_id: str,
        scene_hash: Optional[str] = None,
    ) -> dict:
        """Hash local files, check S3 upload status, and check download status.

        Combines upload and download checks into a single result dict.
        Caches the :class:`SyncPlan` internally so :meth:`upload_files`
        and :meth:`download_files` can proceed without re-checking.
        """
        manager = self._get_sync_manager(farm_id, queue_id)

        # Resolve paths (remove ../ components) — the SDK needs
        # clean absolute paths for grouping and hashing.
        file_paths = [p.resolve() for p in file_paths]

        # Separate files into existing (for upload check) and missing
        # (for download check via manifest lookup).
        existing = [p for p in file_paths if p.exists()]

        # Upload check: hash existing files, check S3.
        if existing:
            plan = manager.prepare_sync(existing)
        else:
            plan = SyncPlan(needs_upload=[], already_synced=[])

        # Download check: match manifest by scene hash, check all
        # manifest files against local filesystem.
        # Use the first file path as scene_path (it's always the
        # scene file from the tracer's flatten() output).
        scene_path = file_paths[0] if file_paths else None
        dl_plan = manager.prepare_download(
            file_paths,
            scene_hash=scene_hash,
            scene_path=scene_path,
        )
        plan.needs_download = dl_plan.needs_download
        plan.download_size_bytes = dl_plan.download_size_bytes

        self._last_plan = plan
        return plan.to_display_dict()

    def upload_files(
        self,
        plan: Optional[SyncPlan] = None,
        on_progress: Optional[Callable[[ProgressInfo], bool]] = None,
        scene_hash: Optional[str] = None,
    ) -> UploadResult:
        """Upload files from the last sync check (or explicit *plan*).

        Args:
            plan: Optional explicit :class:`SyncPlan`.  When *None*,
                uses the plan cached by :meth:`check_sync_status`.
            on_progress: Optional callback receiving
                :class:`ProgressInfo` snapshots.  Return *False* to
                cancel the upload.

        Returns:
            An :class:`UploadResult` with summary statistics.

        Raises:
            RuntimeError: If no plan is available.
        """
        plan = plan or self._last_plan
        if not plan:
            raise RuntimeError(
                "No sync plan available. Run check_sync_status() first."
            )
        if not self._sync_manager:
            raise RuntimeError(
                "No sync manager available. " "Run check_sync_status() first."
            )
        return self._sync_manager.upload_files(
            plan, on_progress, scene_hash=scene_hash
        )

    def check_download_status(
        self,
        file_paths: list[Path],
        farm_id: str,
        queue_id: str,
    ) -> dict:
        """Check which traced files are missing locally but in S3 manifests.

        Caches the plan for :meth:`download_files`.
        """
        manager = self._get_sync_manager(farm_id, queue_id)
        plan = manager.prepare_download(file_paths)
        self._last_plan = plan
        return plan.to_display_dict()

    def download_files(
        self,
        plan: Optional[SyncPlan] = None,
        on_progress: Optional[Callable[[ProgressInfo], bool]] = None,
    ) -> DownloadResult:
        """Download files from S3 CAS identified by the last check.

        Args:
            plan: Optional explicit :class:`SyncPlan`.  When *None*,
                uses the plan cached by :meth:`check_download_status`.
            on_progress: Optional callback receiving
                :class:`ProgressInfo` snapshots.  Return *False* to
                cancel.

        Returns:
            A :class:`DownloadResult` with summary statistics.
        """
        plan = plan or self._last_plan
        if not plan:
            raise RuntimeError(
                "No sync plan available. Run check_download_status() first."
            )
        if not self._sync_manager:
            raise RuntimeError(
                "No sync manager available. "
                "Run check_download_status() first."
            )
        return self._sync_manager.download_files(plan, on_progress)
