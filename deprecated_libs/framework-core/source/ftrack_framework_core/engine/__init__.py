# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

import copy
import time

from ftrack_framework_core.plugin.plugin_info import PluginInfo

import ftrack_constants as constants

from ftrack_utils.decorators import track_framework_usage
from ftrack_framework_core.exceptions.plugin import (
    PluginExecutionError,
    PluginValidationError,
    PluginUIHookExecutionError,
)
from ftrack_framework_core.exceptions.engine import EngineExecutionError


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
    def context_id(self):
        '''
        Returns the context_id where the engine is been executed
        '''
        return self._context_id

    @property
    def plugin_registry(self):
        return self._plugin_registry

    def __init__(
        self,
        plugin_registry,
        session,
        context_id=None,
        on_plugin_executed=None,
    ):
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
        self._context_id = context_id
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

    @track_framework_usage(
        'FRAMEWORK_RUN_PLUGIN',
        {'module': 'engine'},
        ['plugin'],
    )
    def run_plugin(self, plugin, store, options, reference=None):
        '''
        If given *plugin* is in the plugin registry, initialize it with the
        given *options* and execute run method passing given *store* as argument.
        *plugin*: Name of the plugin to be executed.
        *store*: registry of plugin data.
        *options*: options to be passed to the plugin
        *reference*: reference id of the plugin
        '''
        # Specifically checking if its False, as we want to skip the plugin in that case.
        if options.get('enabled') == False:
            self.logger.debug(
                f"Plugin {plugin} is disabled, skipping execution."
            )
            return
        registered_plugin = self.plugin_registry.get_one(name=plugin)

        plugin_instance = registered_plugin['extension'](
            options, self.session, self.context_id
        )
        self.logger.debug(
            f"Run {reference} with options {plugin_instance.options}"
        )

        plugin_info = PluginInfo(
            name=plugin, reference=reference, options=options, store=store
        )

        # Start timer to check the execution time
        start_time = time.time()
        try:
            # Run the plugin
            plugin_instance.run(store)
            plugin_info.status = constants.status.SUCCESS_STATUS
        except PluginExecutionError as error:
            plugin_info.status = constants.status.ERROR_STATUS
            plugin_info.message = f"Error executing {plugin}: {error}"
            # Rise engine error
            raise EngineExecutionError(message=plugin_info.message)

        except PluginValidationError as error:
            plugin_info.status = constants.status.ERROR_STATUS
            plugin_info.message = f"Error validating {plugin}: {error}"
            # logger the message
            self.logger.warning(plugin_info.message)
            try:
                error.attempt_fix(store)
                plugin_info.message += " Succesfully applied fix for plugin"
                plugin_info.status = constants.status.SUCCESS_STATUS
            except Exception as e:
                plugin_info.message += (
                    f" An error occurred while applying the fix: {e}"
                )
                plugin_info.status = constants.status.ERROR_STATUS
                # Rise engine error
                raise EngineExecutionError(message=plugin_info.message)

        except PluginUIHookExecutionError as error:
            plugin_info.status = constants.status.ERROR_STATUS
            plugin_info.message = (
                f"Error executing ui_hook method of {plugin}: {error}"
            )
            # Rise engine error
            raise EngineExecutionError(message=plugin_info.message)

        except Exception as error:
            plugin_info.status = constants.status.ERROR_STATUS
            plugin_info.message = (
                f"Un-handled exception in {plugin},"
                f" with options: {options}. Error: {error}"
            )
            # Rise engine error
            raise EngineExecutionError(message=plugin_info.message)
        finally:
            end_time = time.time()
            total_time = end_time - start_time
            plugin_info.execution_time = total_time
            self.logger.debug(
                f"Result from running plugin {reference}: {plugin_info}"
            )
            if self.on_plugin_executed:
                self.on_plugin_executed(plugin_info.to_dict())

    @track_framework_usage('FRAMEWORK_ENGINE_EXECUTED', {'module': 'engine'})
    def execute_engine(self, engine, user_options):
        '''
        Execute given *engine* from a tool-config.
        *engine*: Portion list of a tool-config with groups and plugins.
        *user_options*: dictionary with options passed by the client to
        the plugins.
        '''

        store = self.get_store()
        for item in engine:
            tool_config_options = user_options.get('options') or {}
            # If plugin is just string execute plugin with no options
            if isinstance(item, str):
                self.run_plugin(item, store, tool_config_options)

            elif isinstance(item, dict):
                if item.get("enabled") == False:
                    continue
                # If it's a group, execute all plugins from the group
                if item["type"] == "group":
                    group_options = copy.deepcopy(tool_config_options)
                    group_options.update(item.get("options") or {})
                    group_reference = item['reference']
                    group_options.update(
                        user_options.get(group_reference) or {}
                    )
                    for plugin_item in item.get("plugins", []):
                        # Use plugin options if plugin is defined as string
                        if isinstance(plugin_item, str):
                            self.run_plugin(plugin_item, store, group_options)
                        else:
                            # Deepcopy the group option to override them for
                            # this plugin
                            options = copy.deepcopy(group_options)
                            options.update(plugin_item.get("options") or {})
                            plugin_reference = plugin_item['reference']
                            options.update(
                                user_options.get(plugin_reference) or {}
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
                    options = copy.deepcopy(tool_config_options)
                    options.update(item.get("options") or {})
                    # Execute plugin only with its own options and tool_config
                    # options if plugin is defined outside the group
                    plugin_reference = item['reference']
                    options.update(user_options.get(plugin_reference) or {})
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
