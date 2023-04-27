import os
from ftrack_connect_pipeline import host, constants, event
import ftrack_api

# Set the minimum required Environment variables.
os.environ['FTRACK_EVENT_PLUGIN_PATH'] = (
    '<path-to-your-repo-folder>/ftrack-connect-pipeline-definition/resource/plugins:'
    '<path-to-your-repo-folder>/ftrack-connect-pipeline-definition/resource/definitions:'
)

# Create a session and Event Manager
session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

# Init host
host_class = host.Host(event_manager)

# Init Client
from ftrack_connect_pipeline import client

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

# Select the File Publisher definition
definition = client_connection.host_connection.definitions[
    'publisher'
].get_all(name='File Publisher')[0]

# Assign the definition to the client
client_connection.change_definition(definition)

# Make the desired changes:
collector_plugins = definition.get_all(category='plugin', type='collector')
collector_plugins[0].options.path = '<Path-to-the-file-to-publish>'
collector_plugins[1].options.path = '<Path-to-the-file-to-publish>'

# Execute the definition.
client_connection.run_definition()

# You could now make more changes and run the definition again to publish a new version.
# collector_plugins = definition.get_all(category='plugin', type='collector')
# collector_plugins[0].options.path='<Path-to-another-file-to-publish>'
# collector_plugins[1].options.path='<Path-to-another-file-to-publish>'
# client_connection.run_definition()
