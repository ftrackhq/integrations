import os
import sys
import ftrack_api
import logging

from Qt import QtWidgets


from ftrack_framework_core.configure_logging import configure_logging

configure_logging(
    'ftrack_framework_standalone',
    extra_modules=["ftrack_qt"],
    propagate=False,
)

logger = logging.getLogger('standalone_ui_test')

ROOT_INTEGRATIONS_FOLDER = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

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
    'extensions/common/framework-engines',
    'extensions/common/framework-plugins',
    'extensions/common/framework-schemas',
    'extensions/common/framework-tool-configs',
    'extensions/common/framework-widgets',
]

for _package in INCLUDE_PACKAGES:
    sys.path.append(os.path.join(ROOT_INTEGRATIONS_FOLDER, _package, "source"))

from ftrack_framework_core import host, event, registry
import ftrack_constants.framework as constants

session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.event.LOCAL_EVENT_MODE
)
os.environ['FTRACK_CONTEXTID'] = '439dc504-a904-11ec-bbac-be6e0a48ed73'
registry_instance = registry.Registry()
registry_instance.scan_modules(
    extension_types=['plugin', 'engine', 'schema', 'tool_config', 'widget'],
    package_names=[
        'ftrack_framework_common_engines',
        'ftrack_framework_common_plugins',
        'ftrack_framework_common_schemas',
        'ftrack_framework_common_tool_configs',
        'ftrack_framework_common_widgets',
        #'sample_photoshop_plugins',
        #'sample_photoshop_tool_configs',
        #'sample_photoshop_widgets',
    ],
)

host_class = host.Host(event_manager, registry=registry_instance)


from ftrack_framework_core import client

client_class = client.Client(event_manager, registry=registry_instance)

app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(sys.argv)

client_class.run_dialog(dialog_name='framework_standard_publisher_dialog')

sys.exit(app.exec_())
