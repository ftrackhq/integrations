# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class FinaliserPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.PLUGIN_FINALISER_TYPE
    required_output_input = [
        'context_id',
        'asset_name',
        'asset_type',
        'comment',
        'status_id'
    ]
