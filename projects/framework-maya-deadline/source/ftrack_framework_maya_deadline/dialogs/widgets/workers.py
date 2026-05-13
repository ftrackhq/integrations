# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""QThread-based workers for async Deadline Cloud operations.

All heavy I/O (AWS API calls, file hashing, S3 checks) runs off
Maya's main thread to keep the UI responsive.  Workers communicate
results back via Qt signals.
"""

import logging

from ftrack_utils.aws.deadline import is_credential_error, is_network_error

from ...utils import QtCore

logger = logging.getLogger(__name__)


class FarmLoadWorker(QtCore.QObject):
    """Load the list of Deadline Cloud farms."""

    farms_loaded = QtCore.Signal(list)
    error = QtCore.Signal(str)
    credential_error = QtCore.Signal(str)

    def __init__(self, deadline_wrapper):
        super().__init__()
        self._wrapper = deadline_wrapper

    def run(self):
        try:
            farms = self._wrapper.list_farms()
            self.farms_loaded.emit(farms)
        except Exception as exc:
            logger.error("Failed to load farms: %s", exc, exc_info=True)
            if is_credential_error(exc):
                self.credential_error.emit(str(exc))
            elif is_network_error(exc):
                self.error.emit(
                    "Cannot connect to AWS. Check your network connection."
                )
            else:
                self.error.emit(str(exc))


class QueueLoadWorker(QtCore.QObject):
    """Load queues for a specific farm."""

    queues_loaded = QtCore.Signal(list)
    error = QtCore.Signal(str)
    credential_error = QtCore.Signal(str)

    def __init__(self, deadline_wrapper, farm_id):
        super().__init__()
        self._wrapper = deadline_wrapper
        self._farm_id = farm_id

    def run(self):
        try:
            queues = self._wrapper.list_queues(self._farm_id)
            self.queues_loaded.emit(queues)
        except Exception as exc:
            logger.error(
                "Failed to load queues for %s: %s",
                self._farm_id,
                exc,
                exc_info=True,
            )
            if is_credential_error(exc):
                self.credential_error.emit(str(exc))
            elif is_network_error(exc):
                self.error.emit(
                    "Cannot connect to AWS. Check your network connection."
                )
            else:
                self.error.emit(str(exc))


class SyncCheckWorker(QtCore.QObject):
    """Hash files and check S3 sync status."""

    progress = QtCore.Signal(str)
    finished = QtCore.Signal(dict)
    error = QtCore.Signal(str)
    credential_error = QtCore.Signal(str)

    def __init__(
        self,
        deadline_wrapper,
        file_paths,
        farm_id,
        queue_id,
        scene_hash=None,
    ):
        super().__init__()
        self._wrapper = deadline_wrapper
        self._file_paths = file_paths
        self._farm_id = farm_id
        self._queue_id = queue_id
        self._scene_hash = scene_hash

    def run(self):
        try:
            self.progress.emit("Hashing files and checking S3...")
            result = self._wrapper.check_sync_status(
                self._file_paths,
                self._farm_id,
                self._queue_id,
                scene_hash=self._scene_hash,
            )
            self.finished.emit(result)
        except FileNotFoundError as exc:
            logger.error("File missing during sync check: %s", exc)
            self.error.emit(f"File not found: {exc.filename or exc}")
        except Exception as exc:
            logger.error("Sync check failed: %s", exc, exc_info=True)
            if is_credential_error(exc):
                self.credential_error.emit(str(exc))
            elif is_network_error(exc):
                self.error.emit(
                    "Cannot connect to AWS. Check your network connection."
                )
            else:
                self.error.emit(str(exc))


class SyncUploadWorker(QtCore.QObject):
    """Upload files to S3 CAS with progress reporting.

    Bridges the deadline SDK's ``on_uploading_assets`` callback
    (which runs on the worker thread) to a Qt signal so the dialog
    can update the UI on the main thread.

    To cancel an in-progress upload, call :meth:`cancel`.  The
    next SDK progress callback will return *False*, causing the
    SDK to raise ``AssetSyncCancelledError``.
    """

    progress = QtCore.Signal(dict)  # ProgressInfo as dict
    finished = QtCore.Signal(dict)  # UploadResult as dict
    error = QtCore.Signal(str)
    credential_error = QtCore.Signal(str)

    def __init__(self, deadline_wrapper, scene_hash=None):
        super().__init__()
        self._wrapper = deadline_wrapper
        self._scene_hash = scene_hash
        self._cancelled = False

    def run(self):
        try:
            result = self._wrapper.upload_files(
                on_progress=self._on_sdk_progress,
                scene_hash=self._scene_hash,
            )
            self.finished.emit(
                {
                    "uploaded_files": result.uploaded_files,
                    "uploaded_bytes": result.uploaded_bytes,
                    "skipped_files": result.skipped_files,
                    "skipped_bytes": result.skipped_bytes,
                    "total_time": result.total_time,
                    "transfer_rate": result.transfer_rate,
                }
            )
        except Exception as exc:
            if "cancelled" in str(exc).lower():
                self.error.emit("Upload cancelled.")
            elif is_credential_error(exc):
                logger.error(
                    "Upload failed (credentials): %s", exc, exc_info=True
                )
                self.credential_error.emit(str(exc))
            elif is_network_error(exc):
                logger.error("Upload failed (network): %s", exc, exc_info=True)
                self.error.emit(
                    "Cannot connect to AWS. Check your network connection."
                )
            else:
                logger.error("Upload failed: %s", exc, exc_info=True)
                self.error.emit(str(exc))

    def _on_sdk_progress(self, info):
        """Bridge ProgressInfo to Qt signal.  Return False to cancel."""
        self.progress.emit(
            {
                "progress": info.progress,
                "message": info.message,
                "processed_files": info.processed_files,
                "transfer_rate": info.transfer_rate,
            }
        )
        return not self._cancelled

    def cancel(self):
        """Request cancellation of the in-progress upload."""
        self._cancelled = True


class SyncDownloadWorker(QtCore.QObject):
    """Download files from S3 CAS with progress reporting."""

    progress = QtCore.Signal(dict)
    finished = QtCore.Signal(dict)
    error = QtCore.Signal(str)
    credential_error = QtCore.Signal(str)

    def __init__(self, deadline_wrapper):
        super().__init__()
        self._wrapper = deadline_wrapper
        self._cancelled = False

    def run(self):
        try:
            result = self._wrapper.download_files(
                on_progress=self._on_sdk_progress,
            )
            self.finished.emit(
                {
                    "downloaded_files": result.downloaded_files,
                    "downloaded_bytes": result.downloaded_bytes,
                    "skipped_files": result.skipped_files,
                    "skipped_bytes": result.skipped_bytes,
                    "total_time": result.total_time,
                    "transfer_rate": result.transfer_rate,
                }
            )
        except Exception as exc:
            if "cancelled" in str(exc).lower():
                self.error.emit("Download cancelled.")
            elif is_credential_error(exc):
                logger.error(
                    "Download failed (credentials): %s", exc, exc_info=True
                )
                self.credential_error.emit(str(exc))
            elif is_network_error(exc):
                logger.error(
                    "Download failed (network): %s", exc, exc_info=True
                )
                self.error.emit(
                    "Cannot connect to AWS. Check your network connection."
                )
            else:
                logger.error("Download failed: %s", exc, exc_info=True)
                self.error.emit(str(exc))

    def _on_sdk_progress(self, info):
        """Bridge ProgressInfo to Qt signal.  Return False to cancel."""
        self.progress.emit(
            {
                "progress": info.progress,
                "message": info.message,
                "processed_files": info.processed_files,
                "transfer_rate": info.transfer_rate,
            }
        )
        return not self._cancelled

    def cancel(self):
        """Request cancellation of the in-progress download."""
        self._cancelled = True


def start_worker(worker, parent=None):
    """Start a worker on a new QThread.

    Returns ``(thread, worker)`` — the caller must hold references to
    both to prevent premature garbage collection (which would crash
    Maya).

    The thread is automatically cleaned up when the worker finishes.
    """
    thread = QtCore.QThread(parent)
    worker.moveToThread(thread)

    # Wire up lifecycle: thread.started -> worker.run,
    # worker done -> thread.quit -> thread.deleteLater.
    thread.started.connect(worker.run)

    # Both finished and error should stop the thread.
    if hasattr(worker, "finished"):
        worker.finished.connect(thread.quit)
    if hasattr(worker, "farms_loaded"):
        worker.farms_loaded.connect(thread.quit)
    if hasattr(worker, "queues_loaded"):
        worker.queues_loaded.connect(thread.quit)
    worker.error.connect(thread.quit)
    if hasattr(worker, "credential_error"):
        worker.credential_error.connect(thread.quit)

    thread.finished.connect(thread.deleteLater)

    thread.start()
    return thread, worker
