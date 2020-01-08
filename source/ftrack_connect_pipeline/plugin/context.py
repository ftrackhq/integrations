# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import BasePlugin


class ContextPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.PLUGIN_CONTEXT_TYPE
    input_options = ['context_id']
    output_options = ['context_id', 'asset_name', 'comment', 'status_id']

    '''def _run(self, event):

        plugin_settings = event['data']['settings']

        # validate input options
        input_valid, message = self.validator.validate_input_options(plugin_settings)
        if not input_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': 0, 'message': str(message)}

        # run Plugin
        start_time = time.time()
        try:
            result = self.run(**plugin_settings)

        except Exception as message:
            end_time = time.time()
            total_time = end_time - start_time
            self.logger.debug(message, exc_info=True)
            return {'status': constants.EXCEPTION_STATUS, 'result': None, 'execution_time': total_time,
                    'message': str(message)}
        end_time = time.time()
        total_time = end_time - start_time

        # validate result with output options
        output_valid, output_valid_message = self.validator.validate_result_options(result)
        if not output_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time,
                    'message': str(output_valid_message)}

        # validate result instance type
        result_type_valid, result_type_valid_message = self.validator.validate_result_type(result)
        if not result_type_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time,
                    'message': str(result_type_valid_message)}

        # Return value is valid
        result_value_valid, result_value_valid_message = self.validator.validate_result_value(result)
        if not result_value_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time,
                    'message': str(result_value_valid_message)}

        return {'status': constants.SUCCESS_STATUS, 'result': result, 'execution_time': total_time,
                'message': 'Successfully run :{}'.format(self.__class__.__name__)}'''