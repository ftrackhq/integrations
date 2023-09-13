# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from abc import ABC, abstractmethod


class BaseEngine(ABC):
    '''
    Base engine class.
    '''

    name = None
    engine_types = ['base']
    '''Engine type for this engine class'''

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`'''
        return self._event_manager

    @property
    def ftrack_object_manager(self):
        '''
        Initializes and returns an instance of
        :class:`~ftrack_framework_core.asset.FtrackObjectManager`
        '''
        return self._ftrack_object_manager

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._host_id

    @property
    def host_types(self):
        '''Return the current host type.'''
        return self._host_types

    def __init__(
        self,
        event_manager,
        ftrack_object_manager,
        host_types,
        host_id,
        asset_type_name=None,
    ):
        '''
        Initialise HostConnection with instance of
        :class:`~ftrack_framework_core.event.EventManager` , and *host*,
        *host_id* and *asset_type_name*

        *host* : Host type.. (ex: python, maya, nuke....)
        *host_id* : Host id.
        *asset_type_name* : If engine is initialized to publish or load, the asset
        type should be specified.
        '''
        super(BaseEngine, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._event_manager = event_manager
        self._ftrack_object_manager = ftrack_object_manager
        self._host_id = host_id
        self._host_types = host_types
        # TODO: double check why and when we need the asset_type_name
        self.asset_type_name = asset_type_name

    @abstractmethod
    def run_plugin(
        self,
        plugin_name,
        plugin_default_method=None,
        plugin_options=None,
        plugin_data=None,
        plugin_context_data=None,
        plugin_method=None,
        plugin_widget_id=None,
        plugin_widget_name=None,
    ):
        '''
        Returns the result of running the plugin with the event returned from
        :meth:`run_event` using the given *plugin*, *plugin_type*,
        *options*, *data*, *context_data*, *method*

        *plugin* : Plugin definition, a dictionary with the plugin information.

        *plugin_type* : Type of plugin.


        *options* : options to pass to the plugin

        *data* : data to pass to the plugin.

        *context_data* : result of the context plugin containing the context_id,
        asset_name... Or None

        *method* : Method of the plugin to be executed.

        '''
        # TODO: Evaluate if plugin_data should better be defined in the
        #  schema, so it can be augmented as well as the options.
        #  (Same for context_data) So basically all the info that the plugin
        #  needs is allways kept in the definition.

        plugin_info = None

        for host_type in reversed(self._host_types):
            plugin_info = self.event_manager.publish.execute_plugin(
                plugin_name,
                plugin_default_method,
                plugin_method,
                host_type,
                plugin_data,
                plugin_options,
                plugin_context_data,
                plugin_widget_id=plugin_widget_id,
                plugin_widget_name=plugin_widget_name,
            )[0]
            break

        if not plugin_info['plugin_boolean_status']:
            self.logger.error(
                "Plugin execution error.\n"
                "Name {} \n"
                "Status {} \n"
                "Method {} \n"
                "Message {} \n"
                "Widget Name {} \n"
                "Result {} \n".format(
                    plugin_info['plugin_name'],
                    plugin_info['plugin_status'],
                    plugin_info['plugin_method'],
                    plugin_info['plugin_message'],
                    plugin_info['plugin_widget_name'],
                    plugin_info['plugin_method_result'],
                )
            )
        return plugin_info

    @abstractmethod
    def run_definition(self, definition):
        '''
        Runs the whole definition from the provided *data*.
        Call the method :meth:`run_step` for each context, component and
        finalizer steps.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run` Should be a
        valid definition.
        '''
        raise NotImplementedError
        # TODO: We can convert definition to a definition object and execute all
        #  plugins as default behaviour....

    @classmethod
    def register(cls, event_manager):
        '''
        Register function for the engine to be discovered.
        '''
        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )

        # subscribe to discover the engine for each compatible type
        for engine_type in cls.engine_types:
            logger.debug(
                'registering: {} for {}'.format(cls.name, engine_type)
            )
            event_manager.subscribe.discover_engine(
                engine_type, cls.name, callback=lambda event: True
            )
