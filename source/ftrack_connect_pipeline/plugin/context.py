# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class ContextPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.PLUGIN_CONTEXT_TYPE
    required_output_options = ['context_id', 'asset_name', 'comment', 'status_id']

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector or empty list.
        Not used, should be Empty

        *options* a dictionary of options passed from outside.

        Returns a Dictionary with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        '''

        required_output_options = ['context_id', 'asset_name', 'comment',
                                   'status_id']

        raise NotImplementedError('Missing run method.')
