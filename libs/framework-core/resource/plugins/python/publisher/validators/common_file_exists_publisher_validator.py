# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonFileExistsPublisherValidatorPlugin(
    plugin.PublisherValidatorPlugin
):
    '''Standalone publisher file validator plugin'''

    plugin_name = 'common_file_exists_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Validate if the file paths provided in *data* exists'''
        output = self.output
        all_files = []
        for plugin_dict in data:
            plugin_result = plugin_dict.get('result')
            all_files.extend(plugin_result)

        if len(all_files) != 0:
            output = True
            for datum in all_files:
                if not os.path.exists(datum):
                    output = False
                    self.logger.error("File {} does not exist".format(datum))

        return output


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonFileExistsPublisherValidatorPlugin(api_object)
    plugin.register()
