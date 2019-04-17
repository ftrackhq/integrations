# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_nuke.plugin import BasenukePlugin, BasenukeWidget


class ImportNukePlugin(BasenukePlugin):
    plugin_type = constants.IMPORTERS


class ImportNukeWidget(BasenukeWidget):
    plugin_type = constants.IMPORTERS

