# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin, BaseWidget


class ImportPlugin(BasePlugin):
    plugin_type = constants.IMPORTERS


class ImportWidget(BaseWidget):
    plugin_type = constants.IMPORTERS

