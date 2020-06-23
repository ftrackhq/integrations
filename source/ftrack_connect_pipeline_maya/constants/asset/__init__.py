# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

FTRACK_ASSET_CLASS_ID = (0x190319)
FTRACK_PLUGIN_TYPE = 'ftrackAssetNode'

#TODO: Check if we have a circular import here as we also import asset ve on the init
from ftrack_connect_pipeline.constants.asset import *
from ftrack_connect_pipeline_maya.constants.asset.v2 import *
from ftrack_connect_pipeline.constants.asset.versions_mapping import *