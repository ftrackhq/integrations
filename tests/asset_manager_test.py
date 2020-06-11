import os
from ftrack_connect_pipeline import host, constants, event
import ftrack_api


from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo, asset_info_from_ftrack_version

from Qt import QtWidgets

import sys

from ftrack_connect_pipeline_qt.asset.asset_info import QFtrackAsset

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline-qt', 'resource', 'application_hook')),
]

app = QtWidgets.QApplication(sys.argv)

from ftrack_connect_pipeline_qt.ui.utility.widget.asset_manager_table import AssetManagerTableView

session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

component_name = 'main'
versions = session.query(
    'select id, components, components.name, components.id, version, asset , asset.name, asset.type.name from '
    'AssetVersion where asset_id != None and components.name is "{0}" limit 30'.format(component_name)
).all()

ftrack_asset_list = []

for version in versions:
    asset_info = asset_info_from_ftrack_version(version, component_name)
    qasset_info = QFtrackAsset(asset_info, session)
    ftrack_asset_list.append(qasset_info)


wid = AssetManagerTableView(ftrack_asset_list, session)
wid.show()
sys.exit(app.exec_())