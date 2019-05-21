# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_nuke.plugin import BaseNukePlugin, BaseNukeWidget


class ImportNukePlugin(BaseNukePlugin):
    plugin_type = constants.IMPORTERS


class ImportNukeWidget(BaseNukeWidget):
    plugin_type = constants.IMPORTERS

