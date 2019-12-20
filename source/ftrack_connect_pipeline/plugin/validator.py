# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class ValidatorPlugin(BasePlugin):
    return_type = bool
    plugin_type = constants.PLUGIN_VALIDATOR_TYPE
    return_value = True
