# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_houdini import plugin
from ftrack_connect_pipeline_houdini import utils as houdini_utils


class HoudiniNativeOpenerFinalizerPlugin(plugin.HoudiniOpenerFinalizerPlugin):
    plugin_name = 'houdini_native_opener_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Save opened Houdini scene to temp to avoid overwrite of published data on DCC save'''
        result = {}

        self.logger.debug('Rename Houdini scene on open')
        save_path, message = houdini_utils.save_scene(
            context_data['context_id'], self.session, save=False
        )
        if save_path:
            result['save_path'] = save_path
        else:
            result = False

        return (result, {'message': message})


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniNativeOpenerFinalizerPlugin(api_object)
    plugin.register()
