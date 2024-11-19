# ftrack Framework Nuke integration release Notes


## v24.11.0rc1
2024-11-19

* [changed] Dependencies; upgrade ftrack dependencies to >=3.0.0
* [changed] Init; Use create_api_session utility to create the api session.
* [changed] Host, Client instance; Pass run_in_main_thread argument.
* [fix] Init; Fix on_run_tool_callback options argument.


## v24.6.0
2024-06-04

* [new] Run setup scene frame range plugin on startup.
* [new] support run tool configs on startup.


## v24.5.0
2024-05-03

* [changed] Replace Qt.py imports to PySide2 and PySide6 on widgets.


## v24.4.1
2024-04-30

* [fix] Launcher; Properly escaped version expressions.


## v24.4.0
2024-04-02

* [changed] When selecting the node to render for reviewable, show all nodes with the selected one on top.
* [new] Writeable node validator, to check if a node is writeable for a reviewable to be created.
* [changed] Upgrade ftrack-framework-core, ftrack-utils and ftrack-qt version.
* [new] Initial release.
