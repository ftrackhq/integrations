
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline import client, host
from ftrack_connect_pipeline import event
import os
import ftrack_api
#os.environ['FTRACK_EVENT_PLUGIN_PATH'] = '/Users/lluisftrack/work/brokenC/ftrack/repos/ftrack-connect-pipeline-definition/resource/application_hook'


#session = get_shared_session('/Users/lluisftrack/work/brokenC/ftrack/repos/ftrack-connect-pipeline-definition/resource/application_hook')


os.environ['FTRACK_EVENT_PLUGIN_PATH'] = '/Users/lluisftrack/work/brokenC/ftrack/repos/ftrack-connect-pipeline-definition/resource/application_hook'
session = ftrack_api.Session()
print session



baseHost = host.initialise(session, host='api', ui=None)
baseClient = client.BasePipelineClient(ui=None, host='api', hostid=baseHost)
print baseClient.packages



'''Lorenzo'''
from ftrack_api import Session
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline import host
from ftrack_connect_pipeline import event
session = Session()
#event_manager = event.EventManager(session, remote=True)
host = host.Host(session, constants.HOST, constants.UI)
host_list = host.discover()
host_id = host_list[0]
client = client.Client(session, constants.HOST, constants.UI, host_id)
publishers = client.fetch('publisher')
model_publisher = publishers[publisher]
model_publisher.components[0]['collectors'][0]['options']['input_path'] = path
client.run(model_publisher)


'''Lorenzo Mod'''
from ftrack_api import Session
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline import host
from ftrack_connect_pipeline import event
session = Session()
#event_manager = event.EventManager(session, remote=True)
host = host.Host(session, constants.HOST, constants.UI)
#host_list = host.discover()
#host_id = host_list[0]
client = client.Client(session, ui, host, hostid=None)
host_l = client.availableHosts()
client.set_host_and_context(host_l[0]['hostid'], host_l[0]['context_id'])
publishers = client.fetch('publisher')
model_publisher = publishers[publisher]
model_publisher.components[0]['collectors'][0]['options']['input_path'] = path
client.run(model_publisher)