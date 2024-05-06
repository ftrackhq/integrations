# ftrack Framework Core library release Notes

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
