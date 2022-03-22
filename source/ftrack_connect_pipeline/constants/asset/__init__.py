# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

#: Name of the ftrack object to identify the loaded assets
FTRACK_OBJECT_NAME = '{}_{}_ftrackdata'
#: LOAD_AS_NODE_ONLY if true when loading an asset only the ftrack node will be
# loaded in the scene, and the asset will apear as unloaded. If false, the
# ftrack node will be created as well but the asset will automatically be added
# (or imported or referenced) in the scene.
# LOAD_AS_NODE_ONLY = True
from ftrack_connect_pipeline.constants.asset.v2 import *
