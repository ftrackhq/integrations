# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


# PLUGINS
class CollectorPlugin(BasePlugin):
    return_type = list
    plugin_type = constants.COLLECTOR


class ValidatorPlugin(BasePlugin):
    return_type = bool
    plugin_type = constants.VALIDATOR
    return_value = True


class OutputPlugin(BasePlugin):
    input_options = ['component_name']
    return_type = dict
    plugin_type = constants.OUTPUT


class PublisherPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.FINALISERS
    output_input = [
        'context_id',
        'asset_name',
        'asset_type',
        'comment',
        'status_id'
    ]
