# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

import pyblish.plugin
import pyblish.api
import pyblish.util

import ftrack_connect_pipeline.ui.display_pyblish_result
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
        self.logger.debug('registering plugin path: %s', path)
        pyblish.plugin.register_plugin_path(path)

    def prepare_publish(self):
        '''Return context for publishing.'''
        context = pyblish.api.Context()
        context = pyblish.util.collect(context=context)
        self.logger.debug('preparing publish with context: %s', context)
        return context

    def update_with_options(
        self, publish_data, item_options, general_options, selected_items
    ):
        '''Update *publish_data* with *item_options* and *general_options*.'''
        self.logger.debug(
            'updating publish_data with options: %s', general_options
        )

        publish_data.data['options'] = general_options
        for instance in publish_data:
            self.logger.debug(
                'updating instance data with : %s', instance
            )

            instance.data['options'] = item_options.get(instance.name, {})
            instance.data['publish'] = instance.name in selected_items

    def publish(self, publish_data):
        '''Publish or raise exception if not valid.'''
        pyblish.util.validate(publish_data)
        pyblish.util.extract(publish_data)
        pyblish.util.integrate(publish_data)

    def show_detailed_result(self, publish_data):
        '''Show detailed results for *publish_data*.'''

        # filter for items with meaningful informations for the users.
        filtered_results = [
            item for item in publish_data.data['results'] if (
                item['error'] or item['records']
            )
        ]
        dialog = ftrack_connect_pipeline.ui.display_pyblish_result.Dialog(
            filtered_results
        )
        dialog.exec_()
