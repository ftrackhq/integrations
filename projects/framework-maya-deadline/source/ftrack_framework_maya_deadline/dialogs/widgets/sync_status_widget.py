# :coding: utf-8
# :copyright: Copyright (c) 2025 ftrack

"""Sync status results widget.

Displays a summary of local-vs-S3 sync status and a collapsible
file tree grouped by "Needs Upload" / "Already Synced".
"""

import logging

from ...utils import QtWidgets, format_bytes

logger = logging.getLogger(__name__)


class SyncStatusWidget(QtWidgets.QWidget):
    """Display sync check results: summary counts and a file tree."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Summary label
        self._summary_label = QtWidgets.QLabel(
            "Click Compare to check sync status."
        )
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        # File tree
        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderLabels(["Path", "Size"])
        self._tree.setColumnWidth(0, 400)
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        layout.addWidget(self._tree)

    # -- Public API ---------------------------------------------------

    def set_results(self, sync_status):
        """Populate from a ``check_sync_status`` result dict."""
        self._tree.clear()

        needs = sync_status.get("needs_upload", [])
        synced = sync_status.get("already_synced", [])
        downloads = sync_status.get("needs_download", [])
        total_size = sync_status.get("total_size_bytes", 0)
        upload_size = sync_status.get("upload_size_bytes", 0)
        download_size = sync_status.get("download_size_bytes", 0)

        # Summary text
        parts = []
        if needs:
            parts.append(
                f"{len(needs)} file(s) need upload "
                f"({format_bytes(upload_size)})"
            )
        if downloads:
            parts.append(
                f"{len(downloads)} file(s) need download "
                f"({format_bytes(download_size)})"
            )
        if synced:
            synced_size = total_size - upload_size - download_size
            parts.append(
                f"{len(synced)} file(s) already synced "
                f"({format_bytes(max(synced_size, 0))})"
            )
        if not needs and not synced and not downloads:
            parts.append("No files found.")

        self._summary_label.setText(" · ".join(parts))

        # "Needs Upload" group
        if needs:
            upload_group = QtWidgets.QTreeWidgetItem(
                self._tree,
                [
                    f"Needs Upload ({len(needs)})",
                    format_bytes(upload_size),
                ],
            )
            upload_group.setExpanded(True)
            for entry in sorted(needs, key=lambda e: e["path"]):
                item = QtWidgets.QTreeWidgetItem(
                    upload_group,
                    [
                        entry["path"],
                        format_bytes(entry["size"]),
                    ],
                )
                item.setToolTip(0, entry["path"])

        # "Needs Download" group
        if downloads:
            download_group = QtWidgets.QTreeWidgetItem(
                self._tree,
                [
                    f"Needs Download ({len(downloads)})",
                    format_bytes(download_size),
                ],
            )
            download_group.setExpanded(True)
            for entry in sorted(downloads, key=lambda e: e["path"]):
                item = QtWidgets.QTreeWidgetItem(
                    download_group,
                    [
                        entry["path"],
                        format_bytes(entry["size"]),
                    ],
                )
                item.setToolTip(0, entry["path"])

        # "Already Synced" group (collapsed by default)
        if synced:
            synced_size = total_size - upload_size - download_size
            synced_group = QtWidgets.QTreeWidgetItem(
                self._tree,
                [
                    f"Already Synced ({len(synced)})",
                    format_bytes(max(synced_size, 0)),
                ],
            )
            synced_group.setExpanded(False)
            for entry in sorted(synced, key=lambda e: e["path"]):
                item = QtWidgets.QTreeWidgetItem(
                    synced_group,
                    [
                        entry["path"],
                        format_bytes(entry["size"]),
                    ],
                )
                item.setToolTip(0, entry["path"])

    def set_loading(self, message):
        """Show a progress message and clear the tree."""
        self._summary_label.setText(message)
        self._tree.clear()

    def set_error(self, message):
        """Show an error message and clear the tree."""
        self._summary_label.setText(f"Error: {message}")
        self._tree.clear()

    def set_upload_complete(self, result):
        """Update display after a successful upload.

        Args:
            result: dict with ``uploaded_files``, ``uploaded_bytes``,
                ``skipped_files``, ``total_time``, ``transfer_rate``.
        """
        uploaded = result.get("uploaded_files", 0)
        uploaded_bytes = result.get("uploaded_bytes", 0)
        skipped = result.get("skipped_files", 0)
        total_time = result.get("total_time", 0)

        parts = []
        if uploaded:
            parts.append(
                f"{uploaded} file(s) uploaded "
                f"({format_bytes(uploaded_bytes)})"
            )
        if skipped:
            parts.append(f"{skipped} file(s) already synced (skipped)")
        if total_time:
            parts.append(f"{total_time:.1f}s")

        self._summary_label.setText(
            "Upload complete: " + " · ".join(parts)
            if parts
            else "Upload complete."
        )

    def clear(self):
        """Reset to initial empty state."""
        self._summary_label.setText("Click Compare to check sync status.")
        self._tree.clear()
