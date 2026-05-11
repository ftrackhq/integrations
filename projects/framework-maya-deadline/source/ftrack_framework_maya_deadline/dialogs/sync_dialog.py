# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Unified Deadline Cloud sync dialog.

Handles both directions (upload and download) and all entry points:

- **Menu / save callback**: non-blocking ``show()``, traces the
  currently open scene via ``MayaSceneTracer``.
- **Pre-open callback**: modal ``exec()`` with Continue / Cancel,
  receives the scene path from ``kBeforeOpenCheck`` so assets can
  be synced before Maya resolves references.
"""

import logging

import maya.cmds as cmds

from ..utils import QtWidgets, QtCore, format_bytes
from .widgets.farm_queue_selector import FarmQueueSelector
from .widgets.sync_status_widget import SyncStatusWidget
from .widgets.workers import SyncCheckWorker, SyncUploadWorker, start_worker

logger = logging.getLogger(__name__)


class DeadlineSyncDialog(QtWidgets.QDialog):
    """Deadline Cloud scene sync dialog.

    Args:
        scene_path: Explicit scene path (used by the pre-open
            callback).  When *None* the dialog reads the current
            scene from ``maya.cmds``.
        modal: When *True* the bottom row shows Continue / Cancel
            instead of Sync / Close.
        parent: Parent QWidget.
    """

    UPLOAD = "upload"
    DOWNLOAD = "download"
    BOTH = "both"

    def __init__(
        self, scene_path=None, modal=False, direction="both", parent=None
    ):
        super().__init__(parent)
        self._explicit_scene_path = scene_path
        self._is_modal = modal
        self._default_direction = direction

        self.setWindowTitle("Deadline Cloud - Sync")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setMinimumSize(600, 450)

        self._deadline_wrapper = None
        self._active_thread = None
        self._active_worker = None

        self._build_ui()

    # -- UI construction ----------------------------------------------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Scene path
        scene_layout = QtWidgets.QHBoxLayout()
        scene_layout.addWidget(QtWidgets.QLabel("Scene:"))
        self._scene_label = QtWidgets.QLabel()
        self._scene_label.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
        )
        scene_layout.addWidget(self._scene_label, 1)
        layout.addLayout(scene_layout)

        self._update_scene_label()

        # Separator
        layout.addWidget(_separator())

        # Farm / queue selector
        self._farm_queue = FarmQueueSelector(self._get_wrapper(), parent=self)
        self._farm_queue.error_occurred.connect(self._on_error)
        layout.addWidget(self._farm_queue)

        # Separator
        layout.addWidget(_separator())

        # Compare row
        compare_layout = QtWidgets.QHBoxLayout()
        self._compare_btn = QtWidgets.QPushButton("Compare")
        self._compare_btn.setToolTip(
            "Trace scene, hash files, and check sync status"
        )
        self._compare_btn.clicked.connect(self._on_compare_clicked)
        compare_layout.addWidget(self._compare_btn)

        self._status_label = QtWidgets.QLabel()
        compare_layout.addWidget(self._status_label, 1)
        layout.addLayout(compare_layout)

        # Results panel
        self._results = SyncStatusWidget(parent=self)
        layout.addWidget(self._results, 1)

        # Progress bar (hidden until upload starts)
        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # Bottom buttons — differ by mode
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        # Direction selector (relates to Sync action)
        self._dir_group = QtWidgets.QButtonGroup(self)
        self._rb_upload = QtWidgets.QRadioButton("Upload")
        self._rb_download = QtWidgets.QRadioButton("Download")
        self._rb_both = QtWidgets.QRadioButton("Both")
        self._dir_group.addButton(self._rb_upload)
        self._dir_group.addButton(self._rb_download)
        self._dir_group.addButton(self._rb_both)
        btn_layout.addWidget(self._rb_upload)
        btn_layout.addWidget(self._rb_download)
        btn_layout.addWidget(self._rb_both)

        {
            self.UPLOAD: self._rb_upload,
            self.DOWNLOAD: self._rb_download,
            self.BOTH: self._rb_both,
        }.get(self._default_direction, self._rb_both).setChecked(True)

        # Sync button (disabled until Compare shows files needing upload)
        self._sync_btn = QtWidgets.QPushButton("Sync")
        self._sync_btn.setEnabled(False)
        self._sync_btn.setToolTip("Upload files to S3 that are not yet synced")
        self._sync_btn.clicked.connect(self._on_sync_clicked)
        btn_layout.addWidget(self._sync_btn)

        # Cancel button (hidden, shown during upload)
        self._cancel_btn = QtWidgets.QPushButton("Cancel")
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        btn_layout.addWidget(self._cancel_btn)

        if self._is_modal:
            # Pre-open mode: Cancel Open / Continue
            cancel_open_btn = QtWidgets.QPushButton("Cancel Open")
            cancel_open_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_open_btn)

            continue_btn = QtWidgets.QPushButton("Continue")
            continue_btn.setDefault(True)
            continue_btn.clicked.connect(self.accept)
            btn_layout.addWidget(continue_btn)
        else:
            # Normal mode: Close
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(self.close)
            btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    @property
    def current_direction(self):
        """Return the selected sync direction."""
        if self._rb_upload.isChecked():
            return self.UPLOAD
        if self._rb_download.isChecked():
            return self.DOWNLOAD
        return self.BOTH

    # -- Lazy wrapper init --------------------------------------------

    def _get_wrapper(self):
        """Return the DeadlineWrapper, creating it on first call."""
        if self._deadline_wrapper is None:
            try:
                from ..wrappers.deadline import DeadlineWrapper

                self._deadline_wrapper = DeadlineWrapper()
            except Exception as exc:
                logger.error(
                    "Failed to create DeadlineWrapper: %s",
                    exc,
                    exc_info=True,
                )
                self._on_error(f"Deadline Cloud SDK not available: {exc}")
                self._deadline_wrapper = _StubWrapper()
        return self._deadline_wrapper

    # -- Compare flow -------------------------------------------------

    def _on_compare_clicked(self):
        """Trace the scene, then kick off async hashing + S3 check."""
        scene_path = self._get_scene_path()
        if not scene_path:
            self._on_error("Scene is not saved. Please save first.")
            return

        self._update_scene_label()

        # Validate farm/queue selection
        farm_id = self._farm_queue.current_farm_id
        queue_id = self._farm_queue.current_queue_id
        if not farm_id or not queue_id:
            self._on_error("Please select a farm and queue.")
            return

        # Trace on main thread (fast — just maya.cmds queries)
        self._status_label.setText("Tracing scene...")
        QtWidgets.QApplication.processEvents()

        try:
            if self._explicit_scene_path:
                # Pre-open: headless parse (scene not loaded in Maya yet)
                from pathlib import Path

                from ..tracer import TraceController

                traced_asset = TraceController.trace(Path(scene_path))
            else:
                # Post-save / menu: live scene query
                from ..tracer.maya_scene_tracer import MayaSceneTracer

                traced_asset = MayaSceneTracer.trace()
        except Exception as exc:
            self._on_error(f"Scene tracing failed: {exc}")
            return

        if not traced_asset.paths:
            self._on_error("Scene is not saved or has no dependencies.")
            return

        file_paths = traced_asset.flatten()
        if not file_paths:
            self._on_error("No files found in scene dependencies.")
            return

        logger.info(
            "Traced %d file(s) from scene. Starting sync check...",
            len(file_paths),
        )

        # Kick off async sync check
        self._set_busy(True)
        self._sync_btn.setEnabled(False)
        self._results.set_loading(
            f"Hashing {len(file_paths)} file(s) and checking S3..."
        )

        worker = SyncCheckWorker(
            self._get_wrapper(), file_paths, farm_id, queue_id
        )
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_compare_finished)
        worker.error.connect(self._on_compare_error)

        self._active_thread, self._active_worker = start_worker(
            worker, parent=self
        )

    def _on_progress(self, message):
        self._status_label.setText(message)

    def _on_compare_finished(self, result):
        self._set_busy(False)
        self._status_label.setText("Done.")
        self._results.set_results(result)

        n_upload = len(result.get("needs_upload", []))
        upload_size = result.get("upload_size_bytes", 0)
        logger.info(
            "Sync check complete: %d file(s) need upload (%s)",
            n_upload,
            format_bytes(upload_size),
        )

        # Enable Sync button when there are files to upload.
        self._sync_btn.setEnabled(n_upload > 0)

    def _on_compare_error(self, message):
        self._set_busy(False)
        self._on_error(message)

    # -- Upload flow --------------------------------------------------

    def _on_sync_clicked(self):
        """Upload files identified by the last Compare."""
        direction = self.current_direction
        if direction == self.DOWNLOAD:
            self._on_error("Download is not yet available.")
            return

        self._set_upload_busy(True)

        worker = SyncUploadWorker(self._get_wrapper())
        worker.progress.connect(self._on_upload_progress)
        worker.finished.connect(self._on_upload_finished)
        worker.error.connect(self._on_upload_error)

        self._active_thread, self._active_worker = start_worker(
            worker, parent=self
        )

    def _on_upload_progress(self, info):
        """Update progress bar and status from SDK callback."""
        self._progress_bar.setValue(int(info["progress"]))
        rate = format_bytes(info["transfer_rate"]) + "/s"
        self._status_label.setText(f'{info["message"]} ({rate})')

    def _on_upload_finished(self, result):
        """Show upload summary."""
        self._set_upload_busy(False)

        uploaded = result["uploaded_files"]
        size = format_bytes(result["uploaded_bytes"])
        time_s = result["total_time"]
        self._status_label.setText(
            f"Upload complete: {uploaded} file(s), {size} " f"in {time_s:.1f}s"
        )
        self._results.set_upload_complete(result)

        # Nothing left to upload after a successful sync.
        self._sync_btn.setEnabled(False)

        logger.info(
            "Upload complete: %d file(s), %s in %.1fs",
            uploaded,
            size,
            time_s,
        )

    def _on_upload_error(self, message):
        self._set_upload_busy(False)
        self._on_error(message)

    def _on_cancel_clicked(self):
        """Request cancellation of the in-progress upload."""
        if self._active_worker and hasattr(self._active_worker, "cancel"):
            self._active_worker.cancel()
            self._status_label.setText("Cancelling...")

    # -- Helpers ------------------------------------------------------

    def _get_scene_path(self):
        """Return the scene path — explicit or from Maya."""
        if self._explicit_scene_path:
            return self._explicit_scene_path
        return cmds.file(q=True, sceneName=True)

    def _update_scene_label(self):
        path = self._get_scene_path()
        self._scene_label.setText(path or "(unsaved)")

    def _set_busy(self, busy):
        self._compare_btn.setEnabled(not busy)
        self._farm_queue.set_enabled(not busy)
        if busy:
            self._status_label.setText("Working...")

    def _set_upload_busy(self, busy):
        """Show/hide progress bar and cancel button during upload."""
        self._progress_bar.setVisible(busy)
        self._progress_bar.setValue(0)
        self._cancel_btn.setVisible(busy)
        self._compare_btn.setEnabled(not busy)
        self._sync_btn.setEnabled(not busy)
        self._farm_queue.set_enabled(not busy)
        if busy:
            self._status_label.setText("Starting upload...")

    def _on_error(self, message):
        # Guard: _on_error can be called from _get_wrapper() during
        # _build_ui() before _status_label / _results are created.
        if hasattr(self, "_status_label"):
            self._status_label.setText("")
        if hasattr(self, "_results"):
            self._results.set_error(message)
        logger.warning("Dialog error: %s", message)

    def showEvent(self, event):
        """Load farms when the dialog is first shown."""
        super().showEvent(event)
        self._update_scene_label()
        if self._farm_queue.current_farm_id is None:
            self._farm_queue.load_farms()


class _StubWrapper:
    """Placeholder when the deadline SDK is unavailable."""

    def get_configured_defaults(self):
        return {"farm_id": None, "queue_id": None}

    def list_farms(self):
        return []

    def list_queues(self, farm_id):
        return []


def _separator():
    """Return a horizontal line widget."""
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line
