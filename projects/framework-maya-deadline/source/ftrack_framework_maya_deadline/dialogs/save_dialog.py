# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Deadline Cloud publish dialog (shell).

Will eventually host scene tracing, comparison, and publish
to S3 / Deadline Cloud.  For now it's a placeholder.
"""

from ..utils import QtWidgets, QtCore


class DeadlineSaveDialog(QtWidgets.QDialog):
    """Publish scene dependencies to Deadline Cloud."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Deadline Cloud - Publish")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        self.setMinimumSize(500, 300)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel("Scene tracing and publish will go here.")
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)

        layout.addStretch()

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignRight)
