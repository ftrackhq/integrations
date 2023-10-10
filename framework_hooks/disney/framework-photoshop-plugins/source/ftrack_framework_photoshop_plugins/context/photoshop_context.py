# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import copy

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class PhotoshopContextPlugin(BasePlugin):
    name = 'photoshop_context'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_CONTEXT_TYPE
    '''Return the given options'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value={
                'context_id': None,
                'asset_name': None,
                'comment': None,
                'status_id': None,
            },
        )

    def run(self, context_data=None, data=None, options=None):
        '''
        Update the required output value with the values of the given *options*
        '''
        required_output = copy.deepcopy(
            self.methods.get('run').get('required_output_value')
        )
        required_output.update(options)
        if not required_output.get('context_id'):
            self.message = (
                "Context error: need context_id provided"
            )
            self.status = constants.status.ERROR_STATUS
            return []
        context_id = required_output['context_id']
        if options.get('status_id') is None:
            # Fixed status
            if 'status_name' not in options:
                self.message = (
                    "Context error: need to specify asset_type_name in options "
                    "when creating a new asset"
                )
                self.status = constants.STATUS_ERROR
                return []
            required_output['status_id'] = self.session.query("Status where name='{}'".format(
                options['status_name'])
            ).one()['id']
        if options.get('asset_id') is None:
            # Create new or load existing asset
            if 'asset_type_name' not in options:
                self.message = (
                    "Context error: need to specify asset_type_name in options "
                    "to enable evaluation of asset"
                )
                self.status = constants.STATUS_ERROR
                return []
            asset_type_name = options['asset_type_name']
            asset_name = options.get('asset_name') or asset_type_name

            # Find asset
            asset = self.session.query('Asset where name is "{}" and type.short is "{}" and parent.id={}'.format(
                asset_name,
                asset_type_name,
                context_id)).first()

            if not asset:
                # Prepare asset creation
                required_output['asset_name'] = options.get('asset_name') or asset_type_name
            else:
                required_output['asset_id'] = asset['id']

        return required_output
