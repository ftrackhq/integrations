# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys

import pyblish.plugin
import pyblish.api
import pyblish.util
import logging

from ftrack_connect_pipeline.ui.publish import display_pyblish_result
from .base import PublishAsset
from ftrack_connect_pipeline import constant


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
        self.pyblish_context = context

        self.logger.debug(
            'Preparing publish with context: {0!r}.'.format(context)
        )

    def update_with_options(
        self, item_options, general_options, selected_items
    ):
        '''Update *item_options* and *general_options*.'''
        self.logger.debug(
            'Update context with options: {0!r}'.format(general_options)
        )

        scene_families = set(constant.SCENE_FAMILY_PYBLISH)

        self.pyblish_context.data['options'] = general_options
        for instance in self.pyblish_context:
            instance.data['options'] = item_options.get(instance.name, {})
            instance.data['publish'] = instance.name in selected_items

            instance_families = set(instance.data['families'])
            if (
                scene_families == instance_families and
                general_options.get(
                    constant.SCENE_AS_REFERENCE_OPTION_NAME, False
                )
            ):
                instance.data['publish'] = True

            self.logger.debug(
                'Updating instance {0!r} with data: {0!r}. Publish flag set to '
                '{0!r}'.format(
                    instance.name, instance.data['options'],
                    instance.data['publish']
                )
            )

    def collect_failed_plugins(self):
        '''Build a list of plugins that failed and error messages.'''
        failed_plugins = []
        for record in self.pyblish_context.data['results']:
            if record['error']:
                failed_plugins.append((
                    record['plugin'].__name__,
                    '@{1}:{3}'.format(*record['error'].traceback)
                ))

        return failed_plugins

    def publish(self, item_options, general_options, selected_items):
        '''Publish or raise exception if not valid.'''
        self.update_with_options(item_options, general_options, selected_items)

        pyblish.util.validate(self.pyblish_context)
        failed_validators = self.collect_failed_plugins()
        if failed_validators:
            return {
                'success': False,
                'stage': 'validation',
                'failed_plugins': failed_validators
            }

        pyblish.util.extract(self.pyblish_context)
        failed_extractors = self.collect_failed_plugins()
        if failed_extractors:
            return {
                'success': False,
                'stage': 'extraction',
                'failed_plugins': failed_extractors
            }

        pyblish.util.integrate(self.pyblish_context)
        failed_integrators = self.collect_failed_plugins()
        if failed_integrators:
            return {
                'success': False,
                'stage': 'integration',
                'failed_plugins': failed_integrators
            }

        return {
            'success': True,
            'asset_version': self.pyblish_context.data.get('asset_version')
        }

    def show_detailed_result(self):
        '''Show detailed results for *publish_data*.'''
        dialog = display_pyblish_result.Dialog(
            self.pyblish_context.data['results']
        )
        dialog.exec_()

    def get_entity(self):
        '''Return the current context entity.'''
        return self.pyblish_context.data['ftrack_entity']

    def switch_entity(self, entity):
        '''Change current context of **publish_data* to the given *entity*.'''
        self.pyblish_context.data['ftrack_entity'] = entity
