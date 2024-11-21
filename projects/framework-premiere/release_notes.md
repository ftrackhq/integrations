# ftrack Framework Premiere integration release Notes


## v24.11.0
2024-11-21

* [changed] Dependencies; Upgrade framework dependencies to version >=3.0.0.
* [changed] Init; Remove remote session and use only one session instead.
* [changed] Init; Use create_api_session utility to create the api session.
* [changed] Host, Client instance; Pass run_in_main_thread argument.
* [fix] Init; Fix on_run_tool_callback options argument.


## v24.6.0
2024-06-04

* [feat] Added support for bootstrap tools run after Premiere connection established.


## v24.5.0
2024-05-13

* [new] Initial implementation with support for publishing a .prproj snapshot with .mp4 reviewable, and opening the .prproj snapshot in Premiere.
