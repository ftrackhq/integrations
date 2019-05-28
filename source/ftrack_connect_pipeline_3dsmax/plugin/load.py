# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_3dsmax.plugin import BaseMaxPlugin, BaseMaxWidget


class ImportMaxPlugin(BaseMaxPlugin):
    plugin_type = constants.IMPORTERS


class ImportMaxWidget(BaseMaxWidget):
    plugin_type = constants.IMPORTERS
