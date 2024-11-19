# ftrack Framework Maya integration release Notes


## v24.11.0rc1
2024-11-19

* [fix] Plugin; Publisher is not launched in docked mode anymore. 
* [changed] Dependencies; upgrade ftrack dependencies to >=3.0.0
* [fix] Plugin; export_type and extension_format correctly propagated.


## v24.10.0
2024-10-29

* [changed] extensions; Playblast override true by default.
* [changed] Dependencies; Update all framework dependencies to version ^3.0.0.
* [fix] Utils; Fix error on importing shiboken2 on utils out of the try/except for PySide6.
* [changed] Init; Use create_api_session utility to create the api session.
* [changed] Host, Client instance; Pass run_in_main_thread argument.
* [fix] Init; Fix on_run_tool_callback options argument.


## v24.6.0
2024-06-04

* [new] Run setup scene frame range plugin on startup. 
* [new] support run tool configs on startup.


## v24.5.0
2024-05-03

* [fix] Launcher; Properly escaped version expressions.
* [changed] Replace Qt.py imports to PySide2 and PySide6 on widgets.

## v24.4.0
2024-04-02

* [changed] maya_export_options_selector widget with all options set to True by default
* [changed] Upgrade ftrack-framework-core, ftrack-utils and ftrack-qt version.
* [new] Initial release.
