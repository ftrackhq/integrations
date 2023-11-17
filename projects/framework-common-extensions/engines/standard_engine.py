# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import copy

from ftrack_framework_engine import BaseEngine


class StandardEngine(BaseEngine):
    '''
    StandardEngine class.
    '''

    name = 'standard_engine'

    def __init__(self, plugin_registry, session, on_plugin_executed=None):
        '''
        Initialise BaseEngine with given *plugin_registry*, *session* and
        optional *on_plugin_executed* callback to communicate with the host.
        '''
        super(StandardEngine, self).__init__(
            plugin_registry, session, on_plugin_executed
        )

    def run_plugin(self, plugin, store, options, reference=None):
        '''
        If given *plugin* is in the plugin registry, initialize it with the
        given *options* and execute run method passing given *store* as argument.
        *plugin*: Name of the plugin to be executed.
        *store*: registry of plugin data.
        *options*: options to be passed to the plugin
        '''
        registered_plugin = self.plugin_registry.get(name=plugin)[0]
        plugin_instance = registered_plugin['extension'](
            options, self.session, reference
        )
        self.logger.debug(
            f"Run {plugin_instance.reference} with options {plugin_instance.options}"
        )
        plugin_info = None
        try:
            plugin_info = plugin_instance.run_plugin(store)
        # TODO: (future improvements) implement a validation error.
        #  except ValidationError as error:
        except Exception as error:
            # TODO: double check if this is necessary as I think is already
            #  handled and printed to the log by the raise Exception.
            self.logger.exception(error)
            raise Exception(
                "Plugin {} can't be executed. Error: {}".format(plugin, error)
            )
        finally:
            if plugin_info:
                if self.on_plugin_executed:
                    self.on_plugin_executed(plugin_info)
                    if not plugin_info['plugin_boolean_status']:
                        raise Exception(
                            "Error executing plugin {}. Error Message {}".format(
                                plugin_info['plugin_name'],
                                plugin_info['plugin_message'],
                            )
                        )
        self.logger.debug(store)

        return plugin_info

    def execute_engine(self, engine, user_options):
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
