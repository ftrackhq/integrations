# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

from ftrack_utils.framework.remote import get_integration_session_id


class PSDocumentOpenerPlugin(BasePlugin):
    name = 'photoshop_document_opener'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_IMPORTER_TYPE
    '''Return the full path of the document passed in the options'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=bool,
            required_output_value=True,
        )

    def run(self, context_data=None, data=None, options=None):
        '''
        Tell Photoshop to open the collected document passed on in *data*.
        '''

        collected_objects = []
        for collector_result in list(
            data[self.plugin_step_name]['collector'].values()
        ):
            collected_objects.extend(collector_result)

        document_path = collected_objects[0]

        if not os.path.exists(document_path):
            self.message = "Document '{}' does not exist!".format(document_path)
            self.status = constants.STATUS_ERROR
            return []

        result = self.event_manager.publish.remote_integration_rpc(
            get_integration_session_id(),
            "openDocument", [document_path],
            fetch_reply=True
        )['result']

        if result is False:
            self.message = "Document open failed!"
            self.status = constants.STATUS_ERROR
            return []
        elif isinstance(result, str):
            self.message = "Error opening document: {}".format(result)
            self.status = constants.STATUS_ERROR
            return []

        return result
