# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Farm and queue cascading dropdown selectors.

Populates from the Deadline Cloud API via background workers and
pre-selects defaults from ``~/.deadline/config``.
"""

import logging

from ...utils import QtWidgets, QtCore
from .workers import FarmLoadWorker, QueueLoadWorker, start_worker

logger = logging.getLogger(__name__)


class FarmQueueSelector(QtWidgets.QWidget):
    """Two-row dropdown selector for Deadline Cloud farm and queue.

    Signals:
        queue_selected(str, str):
            Emitted with ``(farm_id, queue_id)`` whenever a valid
            queue is selected (including after auto-selecting defaults).
        error_occurred(str):
            Emitted when an AWS API call fails.
    """

    queue_selected = QtCore.Signal(str, str)
    error_occurred = QtCore.Signal(str)

    def __init__(self, deadline_wrapper, parent=None):
        super().__init__(parent)
        self._wrapper = deadline_wrapper
        self._defaults = None

        # Hold worker/thread references to prevent GC crashes in Maya.
        self._active_thread = None
        self._active_worker = None

        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Farm row
        layout.addWidget(QtWidgets.QLabel("Farm:"), 0, 0)
        self._farm_combo = QtWidgets.QComboBox()
        self._farm_combo.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        layout.addWidget(self._farm_combo, 0, 1)

        self._farm_refresh = QtWidgets.QPushButton("↻")
        self._farm_refresh.setFixedWidth(30)
        self._farm_refresh.setToolTip("Refresh farms")
        layout.addWidget(self._farm_refresh, 0, 2)

        # Queue row
        layout.addWidget(QtWidgets.QLabel("Queue:"), 1, 0)
        self._queue_combo = QtWidgets.QComboBox()
        self._queue_combo.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        layout.addWidget(self._queue_combo, 1, 1)

        self._queue_refresh = QtWidgets.QPushButton("↻")
        self._queue_refresh.setFixedWidth(30)
        self._queue_refresh.setToolTip("Refresh queues")
        layout.addWidget(self._queue_refresh, 1, 2)

        # Connections
        self._farm_combo.currentIndexChanged.connect(self._on_farm_changed)
        self._queue_combo.currentIndexChanged.connect(self._on_queue_changed)
        self._farm_refresh.clicked.connect(self.load_farms)
        self._queue_refresh.clicked.connect(self._reload_queues)

    # -- Public API ---------------------------------------------------

    @property
    def current_farm_id(self):
        """Return the selected farm ID or *None*."""
        idx = self._farm_combo.currentIndex()
        if idx < 0:
            return None
        return self._farm_combo.itemData(idx)

    @property
    def current_queue_id(self):
        """Return the selected queue ID or *None*."""
        idx = self._queue_combo.currentIndex()
        if idx < 0:
            return None
        return self._queue_combo.itemData(idx)

    def load_farms(self):
        """Kick off an async load of the farms list."""
        self._farm_combo.clear()
        self._farm_combo.addItem("Loading farms...")
        self._farm_combo.setEnabled(False)
        self._queue_combo.clear()
        self._queue_combo.setEnabled(False)

        # Read defaults (synchronous, local config file)
        try:
            self._defaults = self._wrapper.get_configured_defaults()
        except Exception:
            self._defaults = {}

        worker = FarmLoadWorker(self._wrapper)
        worker.farms_loaded.connect(self._on_farms_loaded)
        worker.error.connect(self._on_error)
        self._active_thread, self._active_worker = start_worker(
            worker, parent=self
        )

    def set_enabled(self, enabled):
        """Enable or disable all controls."""
        self._farm_combo.setEnabled(enabled)
        self._queue_combo.setEnabled(enabled)
        self._farm_refresh.setEnabled(enabled)
        self._queue_refresh.setEnabled(enabled)

    # -- Slots --------------------------------------------------------

    def _on_farms_loaded(self, farms):
        self._farm_combo.blockSignals(True)
        self._farm_combo.clear()

        if not farms:
            self._farm_combo.addItem("No farms found")
            self._farm_combo.setEnabled(False)
            self._farm_combo.blockSignals(False)
            return

        default_farm = (self._defaults or {}).get("farm_id")
        select_idx = 0

        for i, farm in enumerate(farms):
            farm_id = farm.get("farmId", "")
            label = farm.get("displayName", farm_id)
            self._farm_combo.addItem(label, farm_id)
            if farm_id == default_farm:
                select_idx = i

        self._farm_combo.setEnabled(True)
        self._farm_combo.blockSignals(False)
        self._farm_combo.setCurrentIndex(select_idx)

    def _on_farm_changed(self, index):
        farm_id = self.current_farm_id
        if not farm_id:
            return
        self._load_queues(farm_id)

    def _reload_queues(self):
        farm_id = self.current_farm_id
        if farm_id:
            self._load_queues(farm_id)

    def _load_queues(self, farm_id):
        self._queue_combo.clear()
        self._queue_combo.addItem("Loading queues...")
        self._queue_combo.setEnabled(False)

        worker = QueueLoadWorker(self._wrapper, farm_id)
        worker.queues_loaded.connect(self._on_queues_loaded)
        worker.error.connect(self._on_error)
        self._active_thread, self._active_worker = start_worker(
            worker, parent=self
        )

    def _on_queues_loaded(self, queues):
        self._queue_combo.blockSignals(True)
        self._queue_combo.clear()

        if not queues:
            self._queue_combo.addItem("No queues found")
            self._queue_combo.setEnabled(False)
            self._queue_combo.blockSignals(False)
            return

        default_queue = (self._defaults or {}).get("queue_id")
        select_idx = 0

        for i, q in enumerate(queues):
            queue_id = q.get("queueId", "")
            label = q.get("displayName", queue_id)
            self._queue_combo.addItem(label, queue_id)
            if queue_id == default_queue:
                select_idx = i

        self._queue_combo.setEnabled(True)
        self._queue_combo.blockSignals(False)
        self._queue_combo.setCurrentIndex(select_idx)

    def _on_queue_changed(self, index):
        farm_id = self.current_farm_id
        queue_id = self.current_queue_id
        if farm_id and queue_id:
            self.queue_selected.emit(farm_id, queue_id)

    def _on_error(self, message):
        self._farm_combo.setEnabled(True)
        self._queue_combo.setEnabled(True)
        self.error_occurred.emit(message)
