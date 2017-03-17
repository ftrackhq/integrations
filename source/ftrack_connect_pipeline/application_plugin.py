# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import abc

import ftrack_api.event.base

import ftrack_connect_pipeline.global_context_switch
import ftrack_connect_pipeline.ui.publish
import ftrack_connect_pipeline.util


class BaseApplicationPlugin(object):
    '''Application plugin.'''

    __metaclass__ = abc.ABCMeta

    def __init__(self, context_id):
        '''Initialise with application *context_id*.'''
        self._context_id = context_id

        self._shared_api_session = None
        self.assets_registered = False

    @property
    def context_entity(self):
        '''Return context.'''
        return self.api_session.get('Context', self._context_id)

    @property
    def api_session(self):
        '''Return the shared api session.'''
        if not self._shared_api_session:
            self._shared_api_session = (
                ftrack_connect_pipeline.util.get_session()
            )

        return self._shared_api_session

    @abc.abstractmethod
    def get_plugin_information(self):
        '''Return plugin information.'''
        # TODO: Update the publisher to use this instead.

    def register_assets(self):
        '''Register assets.'''
        self.api_session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic='ftrack.pipeline.register-assets',
                data=dict()
            ),
            synchronous=True
        )

    def open_publish(self):
        '''Open publish window.'''
        if self.assets_registered is False:
            self.register_assets()

        ftrack_connect_pipeline.ui.publish.open(
            self.api_session
        )

    def open_switch_context(self):
        '''Open switch context dialog.'''
        dialog = ftrack_connect_pipeline.global_context_switch.GlobalSwitch(
            self.context_entity
        )
        self.context_changed.connect(self.set_context)
        dialog.exec_()

    def set_context(self, context_id):
        '''Set context and emit event.'''
        old_context_id = self._context_id
        self._context_id = context_id
        event = ftrack_api.event.base.Event(
            topic='ftrack.context-changed',
            data={'context_id': context_id, 'old_context_id': old_context_id}
        )
        self.api_session.event_hub.publish(event, synchronous=True)
