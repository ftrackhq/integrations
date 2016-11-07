# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys

import pyblish.plugin
import pyblish.api
import pyblish.util
import logging

import ftrack_connect_pipeline.ui.display_pyblish_result
from .base import PublishAsset


class PyblishAsset(PublishAsset):
    '''Publish asset using pyblish module.'''

    def __init__(self, *args, **kwargs):
        '''Instantiate and let pyblish know about the plugins.'''
        super(PyblishAsset, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.register_pyblish_plugin_path()

    def register_pyblish_plugin_path(self):
        '''Register pyblish plugin path.'''
        path = os.path.normpath(
            os.path.join(
                os.path.abspath(
                    os.path.dirname(
                        sys.modules[self.__module__].__file__
                    )
                ),
                'pyblish_plugins'
            )
        )
        logging.debug(
            'Registering pyblish plugin path: {0!r}.'.format(path)
        )
        pyblish.plugin.register_plugin_path(path)

    def prepare_publish(self):
        '''Return context for publishing.'''
        context = pyblish.api.Context()
        context = pyblish.util.collect(context=context)
        self.logger.debug(
            'Preparing publish with context: {0!r}.'.format(context)
        )
        return context

    def update_with_options(
        self, publish_data, item_options, general_options, selected_items
    ):
        '''Update *publish_data* with *item_options* and *general_options*.'''
        self.logger.debug(
            'Updating publish_data with options: {0!r}'.format(general_options)
        )

        publish_data.data['options'] = general_options
        for instance in publish_data:
            instance.data['options'] = item_options.get(instance.name, {})
            instance.data['publish'] = instance.name in selected_items
            self.logger.debug(
                'Updating instance {0!r} with data: {0!r}. Publish flag set to '
                '{0!r}'.format(
                    instance.name, instance.data['options'],
                    instance.data['publish']
                )
            )

    def publish(self, publish_data):
        '''Publish or raise exception if not valid.'''
        pyblish.util.validate(publish_data)
        pyblish.util.extract(publish_data)
        pyblish.util.integrate(publish_data)

        for record in publish_data.data['results']:
            if record['error']:
                self.logger.error(record)

    def show_detailed_result(self, publish_data):
        '''Show detailed results for *publish_data*.'''
        dialog = ftrack_connect_pipeline.ui.display_pyblish_result.Dialog(
            publish_data.data['results']
        )
        dialog.exec_()
