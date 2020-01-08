# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin


class NumericValidatorPlugin(plugin.ValidatorPlugin):
    plugin_name = 'numeric'

    def run(self, context=None, data=None, options=None):
        '''*context* Dictionary with the asset_name, context_id, asset_type, comment and status_id of the asset that
            we are working on. Example: 'context': {u'asset_name': 'PipelineAsset',
                                                    u'context_id': u'529af752-2274-11ea-a019-667d1218a15f',
                                                    'asset_type': u'geo',
                                                     u'comment': 'A new hope',
                                                     u'status_id': u'44dd9fb2-4164-11df-9218-0019bb4983d8'}
            *data* list of data coming from collectors with path of the collected objects
            *options* Dictionary of options added from the ui or manually added. Default is None.
            Return type: Bool
            Returns: Bool
            Required return value to pass validation: True '''
        self.logger.info('data: {}'.format(data))
        test = options.get('test')
        value = options.get('value')

        if len(data) != 1:
            return False

        if test == '>=':
            return int(data[0]) >= int(value)


def register(api_object, **kw):
    plugin = NumericValidatorPlugin(api_object)
    plugin.register()
