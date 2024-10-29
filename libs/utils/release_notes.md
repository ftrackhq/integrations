# ftrack Utils library release Notes

## v3.1.3
2024-10-28

* ~~[fix] Fix collecting tags on progress widget.~~

## v3.1.2
2024-10-28

* [fix] Fix collecting tags on progress widget.


## v3.1.1
2024-10-21

* [fix] Fix temporary file handling which caused issues with the creation of the ftrack menu in Houdini on Windows.


## v3.1.0
2024-09-30

* [changed] framework tool configs; get_groups method dictionary support on filters argument..


## v3.0.1
2024-09-25

* [fix] Calls, decorators; Remove calls package and move the call_directly to decorators threading, this fixes a buc when calling it from framework Client and Host.


## v3.0.0
2024-09-19

* [new] Session, ftrack_api_session; Added create_api_session utility to create the api session with an EventHubThread in case of auto_connect_event_hub is True.
* [new] Dependency; Added dependency on ftrack-python-api.
* [new] event_hub event_hub_thread; Added EventHubThread utility.
* [new] Calls methods; call_directly utility function added to directly call a function with the give arguments.
* [new] Decorators threading; delegate_to_main_thread_wrapper added.
* [new] decorators; run_in_main_thread decorator added.
* [fix] JS RPC; Properly pick up and handle error messages from DCC.
* [changed] get_temp_path; Support temp directories.


## v2.3.0
2024-06-04

* [new] Registry; Support for JS extensions.
* [feat] JS RPC; Added on connected callback.
* [feat] JS RPC; Aligned on_run_dialog_callback with DCC bootstrap implementation.


## v2.2.0
2024-05-02

* [fix] Allow override on dialog/widgets/plugins extensions type.

## v2.1.0
2024-04-02

* [changed] Extensions/environment; Changed the name of FTRACK_EXTENSIONS_PATH environment variable back to FTRACK_FRAMEWORK_EXTENSIONS_PATH.
* [changed] Extensions/registry; Extension type filter support to get_extensions_from_directory.
* [new] Get connect plugin version added on Utils
* [fix] fix track_usage decorator bug. Arguments are correctly queried.


## v2.0.1
2024-03-08

* [changed] get_temp_path util now supports filename_extension with or without leading dot(.)


## v2.0.0
2024-02-12

*  [new] Initial release.
