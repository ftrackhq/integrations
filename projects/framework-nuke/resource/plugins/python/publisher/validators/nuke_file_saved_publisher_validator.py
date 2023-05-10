# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

import nuke

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke import utils as nuke_utils


class NukeFileSavedPublisherValidatorPlugin(
    plugin.NukePublisherValidatorPlugin
):
    '''Nuke file saved publisher validator plugin'''

    plugin_name = 'nuke_file_saved_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return true if the current script is saved'''

        if nuke.Root().name() != 'Root' and nuke.root().modified() != True:
            return True
        else:
            # Attempt to save (snapshot)
            if nuke.Root().name() == 'Root':
                # Save snapshot
                self.logger.debug("Nuke Scene is not saved, saving locally")
                nuke_utils.save_file(context_data['context_id'], self.session)
            else:
                self.logger.debug("Nuke Scene is not saved, saving scene")
                nuke.scriptSave()
            return True
        return False


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeFileSavedPublisherValidatorPlugin(api_object)
    plugin.register()
