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


temp_asset_info ={'asset_id':'123', 'asset_name':'asad', 'asset_type':"vava",
                  'version_id':"2123", 'version_number':"23"}
asset_info = FtrackAssetInfo(temp_asset_info)

temp_asset_info_d ={
    'asset_id':'1a9ad271-6873-4c8c-9567-b2cac15da92e',
    'asset_name':'nukeTest',
    'asset_type':"'Image Sequence'",
    'version_id':"02f21458-10d3-45e6-be78-c7a8e034cc2f",
    'version_number':"34"
}
asset_info_d = FtrackAssetInfo(temp_asset_info_d)


ftrack_asset=QFtrackAsset(asset_info, session)
ftrack_asset_d=QFtrackAsset(asset_info_d, session)

ftrack_asset_list=[]
ftrack_asset_list.append(ftrack_asset)
ftrack_asset_list.append(ftrack_asset_d)

wid = AssetManagerTableView(ftrack_asset_list, session)
wid.show()
sys.exit(app.exec_())