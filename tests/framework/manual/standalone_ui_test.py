import os
import sys
import ftrack_api
import logging

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets


from ftrack_framework_core.configure_logging import configure_logging

configure_logging(
    'ftrack_framework_standalone',
    extra_modules=["ftrack_qt"],
    propagate=True,
)

logger = logging.getLogger('standalone_ui_test')

ROOT_INTEGRATIONS_FOLDER = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
)

INCLUDE_PACKAGES = [
    'libs/framework-core',
    # QT
    'libs/framework-qt' 'libs/qt',
    'libs/qt-style',
    'libs/utils',
]

for _package in INCLUDE_PACKAGES:
    sys.path.append(os.path.join(ROOT_INTEGRATIONS_FOLDER, _package, "source"))

from ftrack_framework_core import host, event, registry
import ftrack_constants.framework as constants

session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.event.LOCAL_EVENT_MODE
)
os.environ[
    'FTRACK_CONTEXTID'
] = '439dc504-a904-11ec-bbac-be6e0a48ed73'  # LLuis
# os.environ['FTRACK_CONTEXTID'] = '571a7a04-eabe-44b5-99b7-6cc5ebb74c77' # Henrik


FTRACK_CONNECT_EXTENSIONS_PATH = [
    os.path.join(
        ROOT_INTEGRATIONS_FOLDER, 'projects', 'framework-common-extensions'
    ),
    os.path.join(ROOT_INTEGRATIONS_FOLDER, 'tests', 'framework', 'resources'),
]

registry_instance = registry.Registry()
registry_instance.scan_extensions(paths=FTRACK_CONNECT_EXTENSIONS_PATH)

host_class = host.Host(event_manager, registry=registry_instance)


from ftrack_framework_core import client

client_class = client.Client(event_manager, registry=registry_instance)

app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(sys.argv)

WHAT = 'publisher'
client_class.run_dialog(
    dialog_name=f'framework_standard_{WHAT}_dialog',
    dialog_options={'tool_configs': [f'standalone-file-{WHAT}']},
)

sys.exit(app.exec_())
