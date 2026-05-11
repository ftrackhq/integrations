# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Data models for AWS Deadline Cloud sync operations.

All models are plain dataclasses — no pydantic, no heavy
dependencies.  They carry the information needed to display sync
status in a UI and to execute uploads without re-hashing.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SyncFileEntry:
    """One file's sync status."""

    path: str
    size: int
    hash: str


@dataclass
class ProgressInfo:
    """Upload progress snapshot.

    Wraps the deadline SDK's ``ProgressReportMetadata`` into a
    framework-neutral form.
    """

    progress: float  # 0-100 percentage
    message: str  # e.g. "Uploaded 1.2 GB / 2.5 GB"
    processed_files: int
    transfer_rate: float  # bytes/sec


@dataclass
class UploadResult:
    """Summary of a completed upload."""

    uploaded_files: int
    uploaded_bytes: int
    skipped_files: int
    skipped_bytes: int
    total_time: float  # seconds
    transfer_rate: float  # bytes/sec


@dataclass
class SyncPlan:
    """Result of :meth:`S3SyncManager.prepare_sync`.

    Holds both *display data* (``needs_upload``, ``already_synced``)
    and *internal state* (``_manifests``, ``_s3_bucket``, …) so that
    :meth:`S3SyncManager.upload_files` can proceed without
    re-hashing.
    """

    needs_upload: list[SyncFileEntry]
    already_synced: list[SyncFileEntry]
    total_files: int
    total_size_bytes: int
    upload_size_bytes: int

    # Internal — retained for upload_files() to avoid re-hashing.
    _manifests: list = field(default_factory=list, repr=False)
    _s3_bucket: str = field(default="", repr=False)
    _root_prefix: str = field(default="", repr=False)
    _cache_directory: str = field(default="", repr=False)

    def to_display_dict(self) -> dict:
        """Return the dict format expected by ``SyncStatusWidget``.

        Backward-compatible with the M4 ``check_sync_status`` return
        value so existing UI code works without changes.
        """
        return {
            "needs_upload": [
                {"path": f.path, "size": f.size, "hash": f.hash}
                for f in self.needs_upload
            ],
            "already_synced": [
                {"path": f.path, "size": f.size, "hash": f.hash}
                for f in self.already_synced
            ],
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "upload_size_bytes": self.upload_size_bytes,
        }
