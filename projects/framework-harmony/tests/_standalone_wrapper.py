# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Bootstrap the Harmony standalone framework process for the tests.

Mirrors what ftrack Connect's ``--run-framework-standalone
ftrack_framework_harmony`` helper process does (a plain module
import, see apps/connect ``__main__.py``), with the dcc-test-harness
server injected first so the tests can inspect the process while it
runs.

The Qt application is created before the server so the server's
main-thread dispatch (QTimer) attaches to the same event loop the
integration runs (``ftrack_framework_harmony`` reuses an existing
QApplication instance).
"""

import os
import sys

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

app = QtWidgets.QApplication(sys.argv)

from dcc_test_harness.server import start  # noqa: E402

start(
    port_file=os.environ["DCC_TEST_PORT_FILE"],
    quit_fn=app.quit,
)

# Bootstraps the integration (ftrack session, Host/Client, registry,
# TCP connection to Harmony) and runs the Qt event loop until quit.
import ftrack_framework_harmony  # noqa: E402,F401
