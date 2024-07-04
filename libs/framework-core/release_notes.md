# ftrack Framework Core library release Notes

## upcoming

* [change] Registry; support get tool config extensions by reference.
* [new] Add method save_tool_config_in_destination in Client; Save given tool config as yaml file in specific destination.
* [new] Add set options to the tool config from the client and dialog.
* [new] Add host_sync_tool_config on event manager to sync tool config from the client to the host.; add sync_tool_config method in the client.; _sync_tool_config_callback method added on Host.


## v2.4.0
2024-06-04

* [fix] Dialog; Properly log exceptions in dialog.
* [new] Registry; Support for JS extensions.


## v2.3.0
2024-05-27

* [changed] Context id passed to the BaseEngine and BasePlugin to know the context where they are executed.
* [new] Add run_tool method on client so can read configs coming from DCC-config file.


## v2.2.1
2024-05-06

* [fix] Registry; Prevent crash if no extensions.


## v2.2.0
2024-05-02

* [fix] Registry; Correctly registering unique objects.


## v2.1.0
2024-04-02

* [new] Registry; extension_types optional argument filter to registry.scan_extensions. 
* [changed] Registry; registry.scan_extensions now support merging of YAML configs, and ignoring (+restoring) duplicate Python extensions(engin, plugin, widget, dialog)
* [fix] launchers config yaml files type value renamed from launchers to launch_config to align to the rest of config files.
* [fix] Fix error on sending mix panel event when run_dialog passing the non serializable docked_func


## v2.0.1
2024-03-08

* [fix] PluginValidationError; Have on_fix_callback as an optional argument.
* [fix] Engine; allow empty options in tool configs.


## v2.0.0
2024-02-12

* [new] Initial release;
