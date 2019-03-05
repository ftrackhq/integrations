from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class ImportPlugin(BasePlugin):
    plugin_type = constants.IMPORTERS

