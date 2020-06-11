import os
from ftrack_connect_pipeline import host, constants, event
import ftrack_api
from ftrack_connect_pipeline_qt.ui.utility.widget.asset_manager_table import AssetManagerTableView

from ftrack_connect_pipeline.asset.asset_info import FtrackAssetInfo

from Qt import QtWidgets

import sys

from ftrack_connect_pipeline_qt.asset.asset_info import QFtrackAsset

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline-qt', 'resource', 'application_hook')),
]

app = QtWidgets.QApplication(sys.argv)

session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

versions = session.query(
    'select asset from AssetVersion where asset_id != None'
).all()

asset_versions = versions[:10]
ftrack_asset_list = []

for version in asset_versions:
    asset_info = FtrackAssetInfo()
    qasset_info = QFtrackAsset(asset_info, session)
    qasset_info.change_version(version['id'])
    ftrack_asset_list.append(qasset_info)


wid = AssetManagerTableView(ftrack_asset_list, session)
wid.show()
sys.exit(app.exec_())