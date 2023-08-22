# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class FileExistsValidatorPlugin(BasePlugin):
    name = 'file_exists_validator'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_VALIDATOR_TYPE
    '''Return the full path of the file passed in the options'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=bool,
            required_output_value=True
        )
        self.register_method(
            method_name='validate',
            required_output_type=bool,
            required_output_value=True
        )

    def validate(self, context_data=None, data=None, options=None):
        collector_result = data['collector_result']
        if type(collector_result) == str:
            collector_result = [data['collector_result']]
        exists = True
        for result in collector_result:
            if not os.path.exists(result):
                exists = False
                break
        return exists

    def run(self, context_data=None, data=None, options=None):

        self.logger.debug("given context_data: {}".format(context_data))
        self.logger.debug("given data: {}".format(data))
        self.logger.debug("given options: {}".format(options))
        # TODO: fix run definitions to be able to pass clear data. We need all
        #  the data from previous executed plugins, but maybe we can convert them
        #  to definition objects or somehow should be easier to get the result
        #  that the client want.
        collector_result = data[0]['result'][0]['result'][0]['plugin_method_result']
        return self.validate(data={'collector_result':collector_result})
