# ftrack Framework Photoshop integration release Notes


## v24.11.0rc1
2024-11-19

* [changed] Dependencies; upgrade ftrack dependencies to >=3.0.0
* [changed] Init; Remove remote session and use only one session instead.
* [changed] Init; Use create_api_session utility to create the api session.
* [changed] Host, Client instance; Pass run_in_main_thread argument.
* [fix] Init; Fix on_run_tool_callback options argument.


## v24.6.0
2024-06-04

* [feat] Added support for bootstrap tools run after Photoshop connection established.


## v24.5.0
2024-05-13

* [fix] Fixed bug where document could not be opened on Windows.
* [changed] Fixed styling bug in panel causing footer to have different grey background.
* [changed] Aligned PS with changes from Premiere, fix CI.
* [changed] Moved extendscript jsx resources to extensions js folder, added PS specific bootstrap extension.
* [changed] Refactored the code to enable code sharing with other Adobe CEP integrations.
* [changed] Replace Qt.py imports to PySide2 and PySide6 on widgets.

## v24.4.1
2024-04-03

* [fix] Prevent re-occurring TASKLIST popup on Windows.

## v24.4.0
2024-04-02

* [changed] Upgrade ftrack-framework-core, ftrack-utils and ftrack-qt version.
* [fix] Fixed path bug on Windows saving .psb files.
* [fix] Fixed bug when publishing an unsaved document causing an exception in collector.
* [new] Initial release.
