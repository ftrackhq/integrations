# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class ContextPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.PLUGIN_CONTEXT_TYPE
    required_input_options = ['context_id']
    required_output_options = ['context_id', 'asset_name', 'comment', 'status_id']
