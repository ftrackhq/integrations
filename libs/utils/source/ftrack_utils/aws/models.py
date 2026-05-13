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
class DownloadResult:
    """Summary of a completed download."""

    downloaded_files: int
    downloaded_bytes: int
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
    needs_download: list[SyncFileEntry] = field(default_factory=list)
    total_files: int = 0
    total_size_bytes: int = 0
    upload_size_bytes: int = 0
    download_size_bytes: int = 0

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
            "needs_download": [
                {"path": f.path, "size": f.size, "hash": f.hash}
                for f in self.needs_download
            ],
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "upload_size_bytes": self.upload_size_bytes,
            "download_size_bytes": self.download_size_bytes,
        }
