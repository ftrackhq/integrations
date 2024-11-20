# ftrack Framework Houdini integration release Notes

## v24.11.0rc1
2024-11-19

* [fix] Plugin; Publisher is not launched in docked mode anymore. 
* [changed] Dependencies; upgrade ftrack dependencies.


## v24.10.1
2024-10-29

* [fix] Connect hook; Fix menu creation and permission errors on launching Houdini.
* [fix] Bootstrap; Fix bootstrap python 3.9 (Houdini 19.0) and python 3.11 (Houdini 20.5)
* [fix] Build; build on python 3.11


## v24.10.0
2024-10-21

* [changed] Build plugin with python 3.10 instead of 3.9
* [changed] Update library versions from version 2 to 3
* [fix] Adjust version expression so Houdini Launchers can be created properly.
* [changed] Init; Use create_api_session utility to create the api session.
* [changed] Host, Client instance; Pass run_in_main_thread argument.
* [fix] Init; Fix on_run_tool_callback options argument.


## v24.6.0
2024-06-26

* [new] Run setup scene frame range plugin on startup.
* [new] Initial release supporting publish and open of Houdini scenes with thumbnail reviewable.
