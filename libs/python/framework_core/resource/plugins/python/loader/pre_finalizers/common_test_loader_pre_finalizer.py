# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommontTestLoaderPreFinalizerPlugin(plugin.LoaderPreFinalizerPlugin):
    '''Loader pre finalizer test/template plugin'''

    plugin_name = 'common_test_loader_pre_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Extract user data and prints them'''
        user_data = None
        for step in data:
            if step['type'] != 'component':
                continue

            for stage in step['result']:
                if stage['type'] != 'post_importer':
                    continue

                user_data = stage['result'][0].get('user_data')

        if user_data:
            print("user_data message: {}".format(user_data.get('message')))
            print("user_data data: {}".format(user_data.get('data')))
        return {}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommontTestLoaderPreFinalizerPlugin(api_object)
    plugin.register()
