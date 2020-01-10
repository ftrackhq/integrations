import os
from ftrack_connect_pipeline import client, host, constants, event
from ftrack_connect_pipeline.session import get_shared_session


CWD = os.path.dirname(__name__)

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook'))
]

# os.environ['FTRACK_EVENT_PLUGIN_PATH'] = os.pathsep.join(event_paths)

# create event manager
session = get_shared_session(plugin_paths=event_paths)

# session = ftrack_api.Session(auto_connect_event_hub=True)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

type(event_manager)

# init host
host.Host(event_manager, host=constants.HOST, extra_hosts_definitions=['maya', 'max'])


# on client ready callback
def ready_callback(hosts):

    host = hosts[0]
    task = host.session.query(
        'select name from Task where project.name is "pipelinetest"'
    ).first()

    schema = task['project']['project_schema']
    task_status = schema.get_statuses('Task')[0]

    publisher = host.definitions['publishers'][0]
    publisher['contexts'][0]['options']['context_id'] = task['id']
    publisher['contexts'][0]['options']['asset_name'] = 'PipelineAsset'
    publisher['contexts'][0]['options']['comment'] = 'A new hope'
    publisher['contexts'][0]['options']['status_id'] = task_status['id']
    publisher['components'][0]['stages'][0]['plugins'][0]['options']['path'] = "/home/ftrackwork/devel/testn11info.nk"
    host.run(publisher)
    # Try The maya publisher
    maya_publisher = host.definitions['publishers'][1]
    maya_publisher['contexts'][0]['options']['context_id'] = task['id']
    maya_publisher['contexts'][0]['options']['asset_name'] = 'PipelineAsset'
    maya_publisher['contexts'][0]['options'][
        'comment'] = 'A new hope from maya plugin'
    maya_publisher['contexts'][0]['options']['status_id'] = task_status['id']
    maya_publisher['components'][0]['stages'][0]['plugins'][0]['options'][
        'path'] = "/Users/lluisftrack/Desktop/file_to_publish.txt"
    host.run(maya_publisher)


# init client
client_connection= client.Client(event_manager, ui=constants.UI)
client_connection.on_ready(ready_callback, time_out=30)

