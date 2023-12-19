# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

import copy
import time

import ftrack_constants as constants


class BaseEngine(object):
    '''
    Base engine class.
    '''

    name = None
    engine_types = ['base']
    '''Engine type for this engine class'''

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._session

    @property
    def plugin_registry(self):
        return self._plugin_registry

    def __init__(self, plugin_registry, session, on_plugin_executed=None):
        '''
        Initialise BaseEngine with given *plugin_registry*, *session* and
        optional *on_plugin_executed* callback to communicate with the host.
        '''
        super(BaseEngine, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._plugin_registry = plugin_registry
        self._session = session
        self.on_plugin_executed = on_plugin_executed

    def get_store(self) -> dict:
        return dict()

    def run_ui_hook(self, plugin, payload, options, reference=None):
        '''
        If given *plugin* is in the plugin registry, initialize it with the
        given *options* and execute the ui_hook method passing given *payload*
        as argument.
        *plugin*: Name of the plugin to be executed.
        *payload*: data.
        *options*: options to be passed to the plugin
        *reference*: reference id of the plugin
        '''
        registered_plugin = self.plugin_registry.get_one(name=plugin)

        plugin_instance = registered_plugin['extension'](options, self.session)
        ui_hook_result = None
        try:
            ui_hook_result = plugin_instance.ui_hook(payload)
        except Exception as error:
            raise Exception(
                "UI hook method of plugin {} can't be executed. Error: {}".format(
                    plugin, error
                )
            )
        finally:
            if ui_hook_result:
                if self.on_plugin_executed:
                    self.on_plugin_executed(ui_hook_result)
        self.logger.debug(
            f"Result from running ui_hook {reference}: {ui_hook_result}"
        )

        return ui_hook_result

    def run_plugin(self, plugin, store, options, reference=None):
        '''
        If given *plugin* is in the plugin registry, initialize it with the
        given *options* and execute run method passing given *store* as argument.
        *plugin*: Name of the plugin to be executed.
        *store*: registry of plugin data.
        *options*: options to be passed to the plugin
        *reference*: reference id of the plugin
        '''
        registered_plugin = self.plugin_registry.get_one(name=plugin)

        plugin_instance = registered_plugin['extension'](options, self.session)
        self.logger.debug(
            f"Run {reference} with options {plugin_instance.options}"
        )

        plugin_info = self.provide_plugin_info(
            plugin,
            reference,
            constants.status.status_bool_mapping[plugin_instance.status],
            plugin_instance.status,
            plugin_instance.message,
            0,
            options,
            store,
        )

        # Start timer to check the execution time
        start_time = time.time()
        try:
            # Set the plugin status to running
            plugin_instance.status = constants.status.RUNNING_STATUS
            # Run the plugin
            result = plugin_instance.run(store)
            # User can return status and message from plugin
            status, message = (None, None) if result is None else result
            # If user did not return status or message.
            if not status:
                status = plugin_instance.status
            if not message:
                message = plugin_instance.message
        except Exception as error:
            if constants.status.status_bool_mapping[plugin_instance.status]:
                plugin_instance.status = constants.status.EXCEPTION_STATUS
            # If status is already handled by the plugin we check if message is
            # also handled if not set a generic one
            if not plugin_instance.message:
                plugin_instance.message = (
                    f"Error executing plugin: {error} \n "
                    f"status {plugin_instance.status}"
                )
            # If both handled by the plugin, logger the message
            self.logger.exception(
                f"Error message: {plugin_instance.message}\n Traceback: {error}"
            )
            plugin_info['plugin_boolean_status'] = False
            plugin_info['plugin_status'] = plugin_instance.status
            plugin_info['plugin_message'] = plugin_instance.message
            if self.on_plugin_executed:
                self.on_plugin_executed(plugin_info)
            return plugin_info

        # print plugin error handled by the plugin
        bool_status = constants.status.status_bool_mapping[status]
        if not bool_status:
            # Generic message in case no message is provided.
            if not message:
                message = (
                    f"Error detected on the plugin {plugin}, "
                    f"but no message provided."
                )
            self.logger.error(message)
            plugin_info['plugin_boolean_status'] = bool_status
            plugin_info['plugin_status'] = status
            plugin_info['plugin_message'] = message
            if self.on_plugin_executed:
                self.on_plugin_executed(plugin_info)
            return plugin_info

        if status == constants.status.RUNNING_STATUS:
            status = constants.status.SUCCESS_STATUS
        full_message = f"Plugin executed, status: {status}, message: {message}"
        end_time = time.time()
        total_time = end_time - start_time
        execution_time = total_time
        self.logger.debug(
            f"Result from running plugin {reference}: {plugin_info}"
        )
        plugin_info['plugin_boolean_status'] = bool_status
        plugin_info['plugin_status'] = status
        plugin_info['plugin_message'] = full_message
        if self.on_plugin_executed:
            self.on_plugin_executed(plugin_info)
        return plugin_info

    def provide_plugin_info(
        self,
        name,
        reference,
        boolean_status,
        status,
        message,
        execution_time,
        options,
        store=None,
    ):
        '''
        Provide the entire plugin information.
        If *store* is given, provides the current store as part of the
        plugin info.
        '''
        return {
            'plugin_name': name,
            'plugin_reference': reference,
            'plugin_boolean_status': boolean_status,
            'plugin_status': status,
            'plugin_message': message,
            'plugin_execution_time': execution_time,
            'plugin_options': options,
            'plugin_store': store,
        }

    def execute_engine(self, engine, user_options):
        '''
        Execute given *engine* from a tool-config.
        *engine*: Portion list of a tool-config with groups and plugins.
        *user_options*: dictionary with options passed by the client to
        the plugins.
        '''
        store = self.get_store()
        for item in engine:
            # If plugin is just string execute plugin with no options
            if isinstance(item, str):
                self.run_plugin(item, store, {})

            elif isinstance(item, dict):
                # If it's a group, execute all plugins from the group
                if item["type"] == "group":
                    group_options = item.get("options", {})
                    group_reference = item['reference']
                    group_options.update(user_options.get(group_reference, {}))
                    for plugin_item in item.get("plugins", []):
                        # Use plugin options if plugin is defined as string
                        if isinstance(plugin_item, str):
                            self.run_plugin(plugin_item, store, group_options)
                        else:
                            # Deepcopy the group option to override them for
                            # this plugin
                            options = copy.deepcopy(group_options)
                            options.update(plugin_item.get("options", {}))
                            plugin_reference = plugin_item['reference']
                            options.update(
                                user_options.get(plugin_reference, {})
                            )
                            self.run_plugin(
                                plugin_item["plugin"],
                                store,
                                # Override group options with the plugin options
                                options,
                                plugin_reference,
                            )
                        # TODO: (future improvements) if group inside a
                        #  group recursively execute plugins inside

                elif item["type"] == "plugin":
                    # Execute plugin only with its own options if plugin is
                    # defined outside the group
                    plugin_reference = item['reference']
                    options = item.get("options", {})
                    options.update(user_options.get(plugin_reference, {}))
                    self.run_plugin(
                        item["plugin"], store, options, plugin_reference
                    )
        return store

    @classmethod
    def register(cls):
        '''
        Register function for the engine to be discovered.
        '''
        import inspect

        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )

        logger.debug(
            'registering: {} for {}'.format(cls.name, cls.engine_types)
        )

        data = {
            'extension_type': 'engine',
            'name': cls.name,
            'extension': cls,
            'path': inspect.getfile(cls),
        }

        return data
