
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



