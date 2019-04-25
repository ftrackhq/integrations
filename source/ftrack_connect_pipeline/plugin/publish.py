# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin, BaseWidget


# PLUGINS
class CollectorPlugin(BasePlugin):
    return_type = list
    plugin_type = constants.COLLECT


class ValidatorPlugin(BasePlugin):
    return_type = bool
    plugin_type = constants.VALIDATE


class OutputPlugin(BasePlugin):
    input_options = ['component_name']
    return_type = dict
    plugin_type = constants.OUTPUT


class PublisherPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.PUBLISH
    output_input = [
        'context_id',
        'asset_name',
        'asset_type',
        'comment',
        'status_id'
    ]


# WIDGET
class CollectorWidget(BaseWidget):
    plugin_type = constants.COLLECT


class ValidatorWidget(BaseWidget):
    plugin_type = constants.VALIDATE


class OutputWidget(BaseWidget):
    plugin_type = constants.OUTPUT


class PublisherWidget(BaseWidget):
    plugin_type = constants.PUBLISH
