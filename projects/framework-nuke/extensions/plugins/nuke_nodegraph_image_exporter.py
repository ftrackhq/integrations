# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
"""Export an image of the Nuke node graph by grabbing its Qt widget off
the screen.

The capture helpers in this module (TCC permission preflight, QScreen
grab, macOS ``screencapture`` fallback) are deliberately self-contained:
Nuke is currently the only integration that screen-grabs a widget - all
other DCCs thumbnail through native APIs (playblast, OpenGL render,
viewport capture, ...). If a second consumer appears, extract them to
``ftrack_qt.utils`` instead of copy-pasting.
"""

import os
import subprocess
import sys

try:
    from PySide6 import QtCore, QtGui
except ImportError:
    from PySide2 import QtCore, QtGui

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_nuke.utils import find_nodegraph_viewer


def ensure_screen_capture_access(logger):
    """On macOS 10.15+, screen capture requires the Screen Recording
    permission. Preflight it and, if absent, request it - which makes the
    OS show its consent dialog the first time this app ever asks.
    Returns True when access is granted (or not applicable)."""
    if sys.platform != "darwin":
        return True
    try:
        import ctypes

        core_graphics = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        preflight = core_graphics.CGPreflightScreenCaptureAccess
        request = core_graphics.CGRequestScreenCaptureAccess
        preflight.restype = ctypes.c_bool
        request.restype = ctypes.c_bool
    except (OSError, AttributeError) as error:
        # Pre-10.15 macOS (no TCC gate for screen capture) or unexpected
        # CoreGraphics layout - let the grab attempt proceed.
        logger.debug(f"Screen capture access preflight unavailable: {error}")
        return True
    if preflight():
        return True
    logger.warning(
        "No macOS Screen Recording permission - requesting access (system "
        "consent dialog is shown on the first ever request)."
    )
    return bool(request())


class NukeNodegraphImageExporterPlugin(BasePlugin):
    """Save an image of the nodegraph to temp location for publish"""

    name = "nuke_nodegraph_image_exporter"

    def get_relative_frame_geometry(self, widget):
        """Get the viewer bounds"""
        fg = widget.frameGeometry()
        left = top = 0
        while True:
            g = widget.geometry()
            left += g.left()
            top += g.top()
            widget = widget.parent()
            if widget is None:
                break
        self.logger.debug(
            "Grab node graph image - relative frame geometry; g.left: {}, g.top: {}".format(
                left, top
            )
        )
        return fg.translated(left, top)

    def screen_capture_widget(self, widget, filename, file_format="png"):
        """Grab the viewer screenshot"""
        if not ensure_screen_capture_access(self.logger):
            raise PluginExecutionError(
                "Nuke has no macOS Screen Recording permission, which is "
                "required to capture the node graph image. Grant it in "
                "System Settings > Privacy & Security > Screen & System "
                "Audio Recording, then relaunch Nuke and publish again."
            )
        rfg = self.get_relative_frame_geometry(widget)
        # QPixmap.grabWindow was removed in Qt6 - use QScreen.grabWindow,
        # which takes the same window id + region arguments.
        window_handle = widget.window().windowHandle()
        screen = window_handle.screen() if window_handle else None
        if screen is None:
            screen = QtGui.QGuiApplication.primaryScreen()
        pixmap = screen.grabWindow(
            widget.winId(),
            rfg.left(),
            rfg.top(),
            rfg.width(),
            rfg.height(),
        )
        self.logger.debug(
            "Grab node graph image - screen; left: {}, top: {}, width: {}, height: {}".format(
                rfg.left(), rfg.top(), rfg.width(), rfg.height()
            )
        )
        if pixmap.isNull() and sys.platform == "darwin":
            # Qt 6.5 (Nuke 16) captures through CGDisplayCreateImageForRect,
            # which Apple obsoleted in macOS 15 (Sequoia) - the grab comes
            # back empty despite Screen Recording permission being granted.
            # Capture the region with the OS screencapture tool instead
            # (ScreenCaptureKit-backed, same permission).
            self.logger.warning(
                "Qt screen grab returned an empty image - falling back to "
                "the macOS screencapture tool."
            )
            self.screen_capture_macos(widget, filename)
            return
        if pixmap.isNull():
            raise PluginExecutionError(
                "Node graph screen grab returned an empty image. Make sure "
                "the node graph panel is visible on screen."
            )
        if not pixmap.save(filename, file_format):
            raise PluginExecutionError(
                f"Failed to write node graph image to: {filename}"
            )

    def screen_capture_macos(self, widget, filename):
        """Capture *widget* to *filename* with the macOS ``screencapture``
        tool, which keeps working on macOS 15+ where the legacy
        CoreGraphics capture used by Qt was obsoleted."""
        global_pos = widget.mapToGlobal(QtCore.QPoint(0, 0))
        region = "{},{},{},{}".format(
            global_pos.x(), global_pos.y(), widget.width(), widget.height()
        )
        self.logger.debug(
            f"Grab node graph image - screencapture region: {region}"
        )
        result = subprocess.run(
            ["/usr/sbin/screencapture", "-x", "-R", region, filename],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise PluginExecutionError(
                'macOS screencapture failed: '
                f'{result.stderr.decode(errors="replace").strip()}'
            )
        if not os.path.exists(filename) or not os.path.getsize(filename):
            raise PluginExecutionError(
                "macOS screencapture produced an empty image. Make sure "
                "Nuke has Screen Recording permission and the node graph "
                "panel is visible on screen."
            )

    def run(self, store):
        """
        Exports a png image of the node graph to the <component> key of the
        given *store*
        """
        component_name = self.options.get("component")
        try:
            view = find_nodegraph_viewer()

        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f"Exception locating viewer to export: {e}"
            )

        try:
            image_path = get_temp_path(filename_extension="png")

            self.screen_capture_widget(view, image_path)
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f"Exception exporting the node graph image: {e}"
            )

        self.logger.debug(f"Exported node graph image to: {image_path}")

        store["components"][component_name]["exported_path"] = image_path
