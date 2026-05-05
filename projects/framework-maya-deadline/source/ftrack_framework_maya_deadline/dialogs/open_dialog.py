# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Deadline Cloud scene status dialog (shell).

When triggered by the kBeforeOpenCheck callback this dialog
runs as a modal (exec()).  The user can sync assets and then
click "Continue" to let Maya proceed, or "Cancel" to abort
the open.

When opened manually from the menu it runs non-blocking
(show()).
"""

from ..utils import QtWidgets, QtCore


class DeadlineOpenDialog(QtWidgets.QDialog):
    """Check scene status against Deadline Cloud."""

    def __init__(self, scene_path=None, parent=None):
        super().__init__(parent)
        self._scene_path = scene_path
        self.setWindowTitle("Deadline Cloud - Scene Status")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setMinimumSize(500, 300)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Scene path info
        if self._scene_path:
            path_label = QtWidgets.QLabel(
                "Opening: {}".format(self._scene_path)
            )
            path_label.setWordWrap(True)
            layout.addWidget(path_label)

        info_label = QtWidgets.QLabel(
            "Scene status and download will go here."
        )
        info_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(info_label)

        layout.addStretch()

        # Button row
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QtWidgets.QPushButton("Cancel Open")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        continue_btn = QtWidgets.QPushButton("Continue")
        continue_btn.setDefault(True)
        continue_btn.clicked.connect(self.accept)
        btn_layout.addWidget(continue_btn)

        layout.addLayout(btn_layout)
