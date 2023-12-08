import os
import sys
import ftrack_api

from ftrack_framework_core import host, event, registry
import ftrack_constants.framework as constants

ROOT_INTEGRATIONS_FOLDER = 'asd'
INCLUDE_PACKAGES = [
    'libs/framework-core',
    'libs/framework-engine',
    'libs/framework-plugin',
    # QT
    'libs/framework-widget',
    'libs/framework-qt' 'libs/qt',
    'libs/qt-style',
    'libs/utils',
]

for _package in INCLUDE_PACKAGES:
    ftrack_package = "ftrack_" + _package.split("/")[-1].replace("-", "_")
    sys.path.append(
        os.path.join(
            ROOT_INTEGRATIONS_FOLDER, _package, "source", ftrack_package
        )
    )

session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.event.LOCAL_EVENT_MODE
)
os.environ['FTRACK_CONTEXTID'] = '439dc504-a904-11ec-bbac-be6e0a48ed73'
FTRACK_FRAMEWORK_EXTENSIONS_PATH = [
    os.path.join(
        ROOT_INTEGRATIONS_FOLDER, 'projects', 'framework-common-extensions'
    )
]

registry_instance = registry.Registry()
registry_instance.scan_extensions(paths=FTRACK_FRAMEWORK_EXTENSIONS_PATH)

host_class = host.Host(event_manager, registry=registry_instance)


from ftrack_framework_core import client

client_class = client.Client(event_manager, registry=registry_instance)

# Get all publisher tool_configs
publisher_tool_configs = client_class.tool_configs['publisher']
# Get the desired tool_config
file_publisher_definiton = publisher_tool_configs.get_first(
    tool_title='File Publisher'
)
# Setup Context plugin options
context_selector_plugin = file_publisher_definiton.get_first(
    category='plugin', plugin_type='context', plugin_title='context selector'
)

context_selector_plugin.options['context_id'] = client_class.context_id
context_selector_plugin.options['asset_name'] = 'file_test'
context_selector_plugin.options['comment'] = 'This is a test from standalone'
context_selector_plugin.options[
    'status_id'
] = '44ddd0fe-4164-11df-9218-0019bb4983d8'

# Configure the collector
file_collector_plugin = file_publisher_definiton.get_first(
    category='plugin', plugin_type='collector', plugin_title='collect file'
)
# This can automatically be provided in the tool_configs. (As well as all the other options)
file_collector_plugin.options['folder_path'] = '/Users/ftrack/Desktop'
file_collector_plugin.options['file_name'] = 'file_collector_test.png'
# Provide folder_path and file_name to publish

client_class.run_tool_config(file_publisher_definiton)
