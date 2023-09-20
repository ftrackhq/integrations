import os
import ftrack_constants as constants
from ftrack_framework_core import event
from ftrack_connect_pipeline_maya import host
import ftrack_api

# Set the minimum required Environment variables.
os.environ['FTRACK_EVENT_PLUGIN_PATH'] = (
    '<path-to-your-repo-folder>/ftrack-connect-pipeline-tool_config/resource/plugins:'
    '<path-to-your-repo-folder>/ftrack-connect-pipeline-tool_config/resource/tool_configs:'
)

# Create a session and Event Manager
session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.event.LOCAL_EVENT_MODE
)

# Init Maya host
host_class = host.MayaHost(event_manager)

# Init Client
from ftrack_framework_core import client

client_connection = client.Client(event_manager)

# Discover hosts
client_connection.discover_hosts()

# Print discovered hosts
# client_connection.host_connections

# Setup a host
client_connection.change_host(client_connection.host_connections[0])

# Set a context id
# You can choose to set the context id in the host or in the client,
# booth ways will work.
host_class.context_id = '<your-context-id>'
# client_connection.context_id = '<your-context-id>'

# Select the File Publisher tool_config
tool_config = client_connection.host_connection.tool_configs[
    'publisher'
].get_all(name='Geometry Publisher')[0]

# Assign the tool_config to the client
client_connection.change_tool_config(tool_config)

# Make the desired changes:
collector_plugins = tool_config.get_all(
    category='plugin', type='collector', name='Geometry Collector'
)
collector_plugins[0].options.collected_objects = ['pCube']
collector_plugins[1].options.collected_objects = ['pCube']
collector_plugins[2].options.collected_objects = ['pCube']

# Execute the tool_config.
client_connection.run_tool_config()
