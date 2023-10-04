import os
import sys
import ftrack_api

from Qt import QtWidgets

ROOT_INTEGRATIONS_FOLDER = 'asd'
INCLUDE_PACKAGES = [
    'libs/framework-core',
    'libs/framework-engine',
    'libs/framework-plugin',
    # QT
    'libs/framework-widget',
    'libs/qt',
    'libs/qt-style',
    'libs/utils',
    # HOOKS
    'framework_hooks/framework-core-engines',
    'framework_hooks/framework-core-plugins',
    'framework_hooks/framework-core-schemas',
    'framework_hooks/framework-core-tool-configs',
]

for _package in INCLUDE_PACKAGES:
    ftrack_package = "ftrack_" + _package.split("/")[-1].replace("-", "_")
    sys.path.append(
        os.path.join(
            ROOT_INTEGRATIONS_FOLDER, _package, "source", ftrack_package
        )
    )

from ftrack_framework_core import host, event
import ftrack_constants.framework as constants

session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.event.LOCAL_EVENT_MODE
)
os.environ['FTRACK_CONTEXTID'] = '439dc504-a904-11ec-bbac-be6e0a48ed73'
host_class = host.Host(event_manager)


from ftrack_framework_core import client

client_class = client.Client(event_manager)

app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(sys.argv)

client_class.run_dialog(dialog_name='framework_publisher_dialog')

sys.exit(app.exec_())
