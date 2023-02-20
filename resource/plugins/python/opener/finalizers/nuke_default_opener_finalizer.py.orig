# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class NukeDefaultOpenerFinalizerPlugin(plugin.NukeOpenerFinalizerPlugin):
    plugin_name = 'nuke_default_opener_finalizer'

    def run(self, context_data=None, data=None, options=None):
        result = {}

        self.logger.debug('Saving Nuke on open')
        save_path, message = nuke_utils.save(
            context_data['context_id'], self.session
        )
        if save_path:
            result['save_path'] = save_path
        else:
            result = False
        self.logger.debug('Initialising Nuke on open')
        nuke_utils.init_nuke(session=self.session)

        return (result, {'message': message})


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeDefaultOpenerFinalizerPlugin(api_object)
    plugin.register()
