"""High-level UI interaction helpers for Qt widget trees.

Provides the ``DCCUI`` class, accessed via the ``dcc_ui`` fixture.
DCC-agnostic: works with any Qt-based application.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

from dcc_test_harness.client import DCCClient, WidgetProxy
from dcc_test_harness.exceptions import WidgetNotFoundError


class DCCUI:
    """High-level DSL for interacting with a DCC's Qt UI.

    Wraps ``DCCClient`` widget methods with convenient helpers
    for dialogs, form filling, and assertions.

    DCC-specific helpers (e.g. Maya menu interaction) should be
    built in the integration project on top of this class or the
    ``DCCClient`` directly.

    Example::

        def test_dialog(dcc_ui):
            dialog = dcc_ui.wait_for_dialog(title="Publisher")
            dcc_ui.fill_form(dialog, {"Comment": "test"})
            dialog.close()
    """

    def __init__(self, client: DCCClient) -> None:
        self._client = client

    # -- Dialog interaction --

    def wait_for_dialog(
        self,
        title: Optional[str] = None,
        widget_type: Optional[str] = None,
        timeout: float = 5.0,
    ) -> WidgetProxy:
        """Wait for a dialog window to appear.

        Raises WidgetNotFoundError if not found within timeout.
        """
        query: dict[str, Any] = {}
        if title is not None:
            query["window_title"] = title
            query["text"] = title
        if widget_type is not None:
            query["widget_type"] = widget_type
        else:
            query["widget_type"] = "QDialog"

        return self._client.wait_for_widget(timeout=timeout, **query)

    def close_all_dialogs(self) -> None:
        """Close all open QDialog instances."""
        self._client.execute(
            """
from PySide6.QtWidgets import QApplication, QDialog
for w in QApplication.topLevelWidgets():
    if isinstance(w, QDialog) and w.isVisible():
        w.close()
"""
        )

    # -- Form filling --

    def fill_form(self, dialog: WidgetProxy, values: dict[str, Any]) -> None:
        """Fill a dialog's form fields by label or objectName.

        Automatically detects widget type and calls the appropriate
        setter. Keys in ``values`` are matched against QLabel text
        or widget objectName.
        """
        widget_id = dialog.widget_id
        values_json = json.dumps(values)

        self._client.execute(
            f"""
import json as _json
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QRadioButton, QSpinBox,
    QDoubleSpinBox, QSlider,
)

dialog = None
for w in QApplication.topLevelWidgets():
    if id(w) == {widget_id}:
        dialog = w
        break

values = _json.loads({values_json!r})
if dialog is None:
    raise RuntimeError("Dialog not found")

labels = dialog.findChildren(QLabel)
for key, value in values.items():
    target = None

    for label in labels:
        if label.text().replace("&", "") == key:
            buddy = label.buddy()
            if buddy:
                target = buddy
                break
            parent = label.parentWidget()
            if parent and parent.layout():
                layout = parent.layout()
                found_label = False
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget() == label:
                        found_label = True
                        continue
                    if found_label and item and item.widget():
                        w = item.widget()
                        if not isinstance(w, QLabel):
                            target = w
                            break
            if target:
                break

    if target is None:
        matches = dialog.findChildren(QWidget, key)
        if matches:
            target = matches[0]

    if target is None:
        continue

    if isinstance(target, QLineEdit):
        target.setText(str(value))
    elif isinstance(target, QTextEdit):
        target.setPlainText(str(value))
    elif isinstance(target, QComboBox):
        if isinstance(value, int):
            target.setCurrentIndex(value)
        else:
            idx = target.findText(str(value))
            if idx >= 0:
                target.setCurrentIndex(idx)
    elif isinstance(target, (QCheckBox, QRadioButton)):
        target.setChecked(bool(value))
    elif isinstance(target, QSpinBox):
        target.setValue(int(value))
    elif isinstance(target, QDoubleSpinBox):
        target.setValue(float(value))
    elif isinstance(target, QSlider):
        target.setValue(int(value))
"""
        )

    # -- Assertions --

    def assert_widget_exists(
        self, timeout: float = 3.0, **query: Any
    ) -> WidgetProxy:
        """Assert a widget exists, waiting up to timeout seconds."""
        try:
            return self._client.wait_for_widget(timeout=timeout, **query)
        except WidgetNotFoundError:
            raise AssertionError(f"Expected widget to exist: {query}")

    def assert_widget_not_exists(
        self, timeout: float = 1.0, **query: Any
    ) -> None:
        """Assert no widget matches the query after waiting."""
        widget = self._client.find_widget(**query)
        if widget is not None:
            time.sleep(timeout)
            widget = self._client.find_widget(**query)
            if widget is not None:
                raise AssertionError(f"Expected widget to not exist: {query}")

    def assert_widget_text(self, expected: str, **query: Any) -> None:
        """Assert a widget's text matches the expected value."""
        widget = self._client.find_widget(**query)
        if widget is None:
            raise AssertionError(f"Widget not found: {query}")
        widget.refresh()
        actual = widget.text
        if actual != expected:
            raise AssertionError(f"Expected text {expected!r}, got {actual!r}")

    def assert_widget_visible(self, **query: Any) -> None:
        """Assert a widget is visible."""
        widget = self._client.find_widget(**query)
        if widget is None:
            raise AssertionError(f"Widget not found: {query}")
        widget.refresh()
        if not widget.visible:
            raise AssertionError(f"Expected widget to be visible: {query}")

    def assert_widget_enabled(self, **query: Any) -> None:
        """Assert a widget is enabled."""
        widget = self._client.find_widget(**query)
        if widget is None:
            raise AssertionError(f"Widget not found: {query}")
        widget.refresh()
        if not widget.enabled:
            raise AssertionError(f"Expected widget to be enabled: {query}")
