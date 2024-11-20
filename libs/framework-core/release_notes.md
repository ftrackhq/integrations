# ftrack Framework Core library release Notes


## v3.2.1
2024-11-20

* [changed] Log; Set save of log file warning to info level.

## v3.2.0
2024-11-19

* [changed] Registry; Remove support for JS extensions.


## v3.1.2
2024-10-28

* [fix] Host; Create new session when running a tool config to avoid corrupted sessions.


## v3.1.1
2024-10-04

* [fix] Host; Fix bug on set context_id calling the run_in_main_thread_wrapper.


## v3.1.0
2024-09-30

* [change] Registry; Support get tool config extensions by reference.
* [change] Registry; Support create references in a tool-config section.


## v3.0.1
2024-09-25

* [fix] Client, Host; Fix issue with run_in_main_thread_wrapper decorator.


## v3.0.0
2024-09-19

* [changed] Host; Remove with_new_session decorator and use current remote session directly.
* [changed] EventManager; Remove the ability to connect to the event hub, instead assume that passed session argument is already connected.
* [changed] EventManager; EventHubThread moved to ftrack_utils.
* [new] Client, Host; Using delegate_to_main_thread_wrapper decorator to execute methods in main thread function provided as run_in_main_thread_wrapper argument when instantiating.
* [change] EventManager; Remove override mode.
* [feature] Client, Engine, Dialog; Support tool config top level options.
* [fix] Engine; Check enabled/disabled plugins.
* [change] Client, Dialog; Support set_tool_config_option for any item in the tool_conifg.


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
