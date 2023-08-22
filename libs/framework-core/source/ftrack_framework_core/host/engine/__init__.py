# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

# TODO: verify that we use this instead of constants
#  This works, the problem is that you already have to had imported the modules
#  with the subclasses before in that moment, getEngine will work, so this can
#  be useful for later when splitting the engines
def getEngine(baseClass, engineType):
    '''
    Returns the Class or Subclass of the given *baseClass* that matches the
    name of the given *engineType*
    '''
    for subclass in baseClass.__subclasses__():
        # TODO: make this read multiple types so engine type can be a list
        if engineType == subclass.__name__:
            return subclass
        match = getEngine(subclass, engineType)
        if match:
            return match


# TODO: separate engines to its own module
class BaseEngine(object):
    '''
    Base engine class.
    '''

    engine_type = ['base']
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
            self, event_manager, ftrack_object_manager, host_types, host_id,
            asset_type_name
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


    # TODO: this should be an ABC
    def run_plugin(
        self,
        plugin_name,
        plugin_default_method=None,
        plugin_options=None,
        plugin_data=None,
        plugin_context_data=None,
        plugin_method=None,
        plugin_widget_id=None,
        plugin_widget_name=None
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
        aset_name... Or None

        *method* : Method of the plugin to be executed.

        '''
        plugin_info = None

        for host_type in reversed(self._host_types):
            plugin_info = self.event_manager.publish.execute_plugin(
                plugin_name, plugin_default_method, plugin_method, host_type, plugin_data,
                plugin_options, plugin_context_data,
                plugin_widget_id=plugin_widget_id,
                plugin_widget_name=plugin_widget_name
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


    #TODO: This should be an ABC
    def run_definition(self, definition_data):
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
