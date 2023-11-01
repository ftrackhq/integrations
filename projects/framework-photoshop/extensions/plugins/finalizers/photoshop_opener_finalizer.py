# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_integration_session_id


class PhotoshopOpenerFinalizer(BasePlugin):
    name = 'photoshop_opener_finalizer'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_FINALIZER_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''
        Tell Photoshop to rename the newly opened snapshot to a temp path, to
        protect original published file from being overwritten.
        '''

        temp_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.psd'
        ).name

        self.logger.debug(
            'Telling Photoshop to save document to: {}'.format(temp_path)
        )

        result = self.event_manager.publish.remote_integration_rpc(
            get_integration_session_id(),
            "saveDocument",
            [temp_path],
            fetch_reply=True,
        )['result']

        if not result:
            self.message = "Document save to temp failed!"
            self.status = constants.status.ERROR_STATUS
            return {}
        elif isinstance(result, str):
            self.message = "Could not save document to temp: {}".format(result)
            self.status = constants.status.ERROR_STATUS
            return {}
        return {'path': temp_path}
