# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class OutputPlugin(BasePlugin):
    input_options = ['component_name']
    return_type = dict
    plugin_type = constants.PLUGIN_OUTPUT_TYPE