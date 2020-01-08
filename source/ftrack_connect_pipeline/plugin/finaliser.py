# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class FinaliserPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.PLUGIN_FINALISER_TYPE
    required_output_options = [
        'context_id',
        'asset_name',
        'asset_type',
        'comment',
        'status_id'
    ]

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from outputs.

        *options* a dictionary of options passed from outside.

        Returns a Dictionary with ontext_id, asset_name, asset_type, comment, status_id.

        '''

        raise NotImplementedError('Missing run method.')