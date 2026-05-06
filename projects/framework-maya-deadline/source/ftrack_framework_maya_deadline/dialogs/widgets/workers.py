# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""QThread-based workers for async Deadline Cloud operations.

All heavy I/O (AWS API calls, file hashing, S3 checks) runs off
Maya's main thread to keep the UI responsive.  Workers communicate
results back via Qt signals.
"""

import logging

from ...utils import QtCore

logger = logging.getLogger(__name__)


class FarmLoadWorker(QtCore.QObject):
    """Load the list of Deadline Cloud farms."""

    farms_loaded = QtCore.Signal(list)
    error = QtCore.Signal(str)

    def __init__(self, deadline_wrapper):
        super().__init__()
        self._wrapper = deadline_wrapper

    def run(self):
        try:
            farms = self._wrapper.list_farms()
            self.farms_loaded.emit(farms)
        except Exception as exc:
            logger.error("Failed to load farms: %s", exc, exc_info=True)
            self.error.emit(str(exc))


class QueueLoadWorker(QtCore.QObject):
    """Load queues for a specific farm."""

    queues_loaded = QtCore.Signal(list)
    error = QtCore.Signal(str)

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
            self.error.emit(str(exc))


class SyncCheckWorker(QtCore.QObject):
    """Hash files and check S3 sync status."""

    progress = QtCore.Signal(str)
    finished = QtCore.Signal(dict)
    error = QtCore.Signal(str)

    def __init__(self, deadline_wrapper, file_paths, farm_id, queue_id):
        super().__init__()
        self._wrapper = deadline_wrapper
        self._file_paths = file_paths
        self._farm_id = farm_id
        self._queue_id = queue_id

    def run(self):
        try:
            self.progress.emit("Hashing files and checking S3...")
            result = self._wrapper.check_sync_status(
                self._file_paths,
                self._farm_id,
                self._queue_id,
            )
            self.finished.emit(result)
        except Exception as exc:
            logger.error("Sync check failed: %s", exc, exc_info=True)
            self.error.emit(str(exc))


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

    thread.finished.connect(thread.deleteLater)

    thread.start()
    return thread, worker
