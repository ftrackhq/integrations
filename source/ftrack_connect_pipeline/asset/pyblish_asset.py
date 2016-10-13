import os

import pyblish.plugin
import pyblish.api
import pyblish.util

from .base import PublishAsset


class PyblishAsset(PublishAsset):
    '''Publish asset using pyblish module.'''

    def __init__(self, *args, **kwargs):
        '''Instantiate and let pyblish know about the plugins.'''
        super(PyblishAsset, self).__init__(*args, **kwargs)
        self.register_pyblish_plugin_path()

    def register_pyblish_plugin_path(self):
        '''Register pyblish plugin path.'''
        path = os.path.normpath(
            os.path.join(
                os.path.abspath(
                    os.path.dirname(__file__)
                ),
                '..',
                'pyblish_plugin'
            )
        )
        pyblish.plugin.register_plugin_path(path)

    def prepare_publish(self):
        '''Return context for publishing.'''
        context = pyblish.api.Context()
        context = pyblish.util.collect(context=context)
        return context

    def update_with_options(
        self, publish_data, item_options, general_options, selected_items
    ):
        '''Update *publish_data* with *item_options* and *general_options*.'''
        publish_data.data['options'] = general_options
        print 'DATA!'
        print publish_data.data
        print publish_data.data['options']

        for instance in publish_data:
            instance.data['options'] = item_options.get(instance.id, {})
            instance.data['publish'] = instance.id in selected_items
            print(
                instance.id, instance.data['publish'], instance.data['options']
            )

    def publish(self, publish_data):
        '''Publish or raise exception if not valid.'''
        pyblish.util.validate(publish_data)
        pyblish.util.extract(publish_data)
        pyblish.util.integrate(publish_data)
