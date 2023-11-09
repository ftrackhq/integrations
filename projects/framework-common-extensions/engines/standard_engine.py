# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import copy

from ftrack_framework_engine import BaseEngine
from ftrack_utils.deocrators import with_session


class StandardEngine(BaseEngine):
    '''
    StandardEngine class.
    '''

    name = 'standard_engine'

    def __init__(self, plugin_registry):
        '''
        Initialise StandardEngine with given *plugin_registry*.
        '''
        super(StandardEngine, self).__init__(plugin_registry)

    @with_session
    def run_plugin(self, plugin, store, options, session=None):
        '''
        If given *plugin* is in the plugin registry, initialize it with the
        given *options* and execute run method passing given *store* as argument.
        *plugin*: Name of the plugin to be executed.
        *store*: registry of plugin data.
        *options*: options to be passed to the plugin
        '''
        registered_plugin = self.plugin_registry.get(name=plugin)[0]
        plugin_instance = registered_plugin['cls'](options, session)
        print(
            f"Run {plugin_instance.id} with options {plugin_instance.options}"
        )
        # try:
        plugin_info = plugin_instance.run_plugin(store)
        # TODO: (future improvements) implement a validation error.
        #  except ValidationError as error:
        # except Exception as error:
        # TODO: implement the exception error. Log and rise?
        # pass
        # if self.on_plugin_execution_success:
        # self.on_plugin_execution_success(
        # execution_time
        # )
        # return result
        print(store)
        print("*" * 10)
        # TODO: think on where do we add the notify client if the engine doesn't
        #  have the event manager either.
        # def _notify_client(self):
        #     '''Publish an event with the plugin info to be picked by the client'''
        #     self.event_manager.publish.notify_plugin_progress_client(
        #         self.provide_plugin_info()
        #     )

    def execute_engine(self, engine):
        '''
        Execute given *engine* from a tool-config.
        *engine*: Portion list of a tool-config with groups and plugins.
        '''
        store = dict()
        for item in engine:
            # If plugin is just string execute plugin with no options
            if isinstance(item, str):
                self.run_plugin(item, store, {})

            elif isinstance(item, dict):
                # TODO: temp solution, evaluate if to use lists.
                if item.get('options') and isinstance(
                    item.get('options'), list
                ):
                    item['options'] = {
                        k: v
                        for _dict in item['options']
                        for k, v in _dict.items()
                    }
                # If it's a group, execute all plugins from the group
                if item["type"] == "group":
                    group_options = item.get("options", {})
                    for plugin_item in item.get("plugins", []):
                        # Use plugin options if plugin is defined as string
                        if isinstance(plugin_item, str):
                            self.run_plugin(plugin_item, store, group_options)
                        else:
                            # TODO: temporal solution evaluate if to use list
                            if plugin_item.get("options") and isinstance(
                                plugin_item.get("options"), list
                            ):
                                plugin_item['options'] = {
                                    k: v
                                    for _dict in plugin_item['options']
                                    for k, v in _dict.items()
                                }
                            # Deepcopy the group option to override them for
                            # this plugin
                            options = copy.deepcopy(group_options)
                            self.run_plugin(
                                plugin_item["plugin"],
                                store,
                                # Override group options with the plugin options
                                options.update(plugin_item.get("options", {})),
                            )
                        # TODO: (future improvements) if group inside a
                        #  group recursively execute plugins inside

                elif item["type"] == "plugin":
                    # Execute plugin only with its own options if plugin is
                    # defined outside the group
                    self.run_plugin(
                        item["plugin"], store, item.get("options", {})
                    )
