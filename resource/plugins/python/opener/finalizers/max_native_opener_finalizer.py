# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils


class MaxNativeOpenerFinalizerPlugin(plugin.MaxOpenerFinalizerPlugin):
    plugin_name = 'max_native_opener_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Save opened Max scene in temp to avoid being overwritten'''

        result = {}

        self.logger.debug('Save Max scene to temp on open')
        save_path, message = max_utils.save_file(
            None,
            context_id=context_data['context_id'],
            session=self.session,
            save=True,
        )
        if save_path:
            result['save_path'] = save_path
        else:
            result = False

        return result, {'message': message}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxNativeOpenerFinalizerPlugin(api_object)
    plugin.register()
