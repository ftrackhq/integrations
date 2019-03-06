# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_maya.plugin import BaseMayaPlugin, BaseMayaWidget


class ImportMayaPlugin(BaseMayaPlugin):
    plugin_type = constants.IMPORTERS


class ImportMayaWidget(BaseMayaWidget):
    plugin_type = constants.IMPORTERS

