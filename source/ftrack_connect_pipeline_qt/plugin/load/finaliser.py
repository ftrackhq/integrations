# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt.plugin import base


class LoaderFinaliserWidget(base.BaseFinaliserWidget):
    plugin_type = constants.PLUGIN_LOADER_FINALISER_TYPE
