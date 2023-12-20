# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

import copy
import time

from ftrack_framework_core.plugin.plugin_info import PluginInfo

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

        plugin_info = PluginInfo(
            name=plugin, reference=reference, options=options, store=store
        )

        # Start timer to check the execution time
        start_time = time.time()
        try:
            # Set the plugin status to running
            plugin_info.status = constants.status.RUNNING_STATUS
            # Run the plugin
            result = plugin_instance.run(store)
            # Validate the result tuple
            if self.is_valid_plugin_result(result):
                if result and result != (None, None):
                    plugin_info.status = result[0]
                    plugin_info.message = result[1]
                else:
                    plugin_info.status = constants.status.SUCCESS_STATUS
            else:
                raise ValueError(
                    f"Invalid plugin result format, expected a valid string "
                    f"status and message but got {result}"
                )
        except Exception as error:
            plugin_info.status = constants.status.EXCEPTION_STATUS

            plugin_info.message = (
                f"Error executing plugin: {error} \n "
                f"status {plugin_info.status}"
            )
            # logger the message
            self.logger.exception(
                f"Error message: {plugin_instance.message}\n Traceback: {error}"
            )

            if self.on_plugin_executed:
                self.on_plugin_executed(plugin_info.to_dict())
            return plugin_info.to_dict()

        # print plugin error handled by the plugin
        if not plugin_info.boolean_status:
            # Generic message in case no message is provided.
            if not plugin_info.message:
                plugin_info.message = (
                    f"Error detected on the plugin {plugin}, "
                    f"but no message provided."
                )
            self.logger.error(plugin_info.message)
            if self.on_plugin_executed:
                self.on_plugin_executed(plugin_info.to_dict())
            return plugin_info
        plugin_info.status = constants.status.SUCCESS_STATUS

        plugin_info.message = (
            f"Plugin executed, status: {plugin_info.status}, "
            f"message: {plugin_info.message}"
        )
        end_time = time.time()
        total_time = end_time - start_time
        plugin_info.execution_time = total_time
        self.logger.debug(
            f"Result from running plugin {reference}: {plugin_info}"
        )
        if self.on_plugin_executed:
            self.on_plugin_executed(plugin_info.to_dict())
        return plugin_info

    def is_valid_plugin_result(self, result):
        '''
        Validates if the result is a tuple with valid status and message.

        :param result: Result tuple to validate.
        :type result: tuple
        :return: True if valid, False otherwise.
        :rtype: bool
        '''
        if not result or result == (None, None):
            return True
        if not isinstance(result, tuple) and len(result) != 2:
            self.logger.error(
                f"Invalid plugin result format. "
                f"Expected tuple with status and message, got {result}"
            )
            return False
        if not isinstance(result[0], str) or not isinstance(result[1], str):
            self.logger.error(
                f"Invalid plugin result format. "
                f"Expected string status and string message, "
                f"got: \n status: {result[0]} type: {type(result[0])},\n "
                f"message: {result[0]}, type: {type(result[0])}"
            )
            return False
        if not result[0] in constants.status.STATUS_LIST:
            self.logger.error(
                f"Invalid plugin result format. "
                f"Expected status {constants.status.STATUS_LIST}, "
                f"got: {result[0]}"
            )
            return False
        return True

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
