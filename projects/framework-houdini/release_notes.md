# ftrack Framework Houdini integration release Notes

## v26.7.0rc1
2026-06-29

* [changed] Branding; capitalized user-facing "ftrack" labels and dialog/window titles to "Ftrack", including the Houdini main menu.
* [fix] Menu; Refresh the Houdini startup search-path cache after writing the menu file so the ftrack menu appears on Houdini 21+. Houdini 21 caches search paths early in startup and otherwise never discovers the dynamically generated MainMenuCommon.xml.
* [changed] Python panel; Docked Python panel left disabled (publisher floats, consistent with the other DCC integrations); embedding the dialog into a Houdini Python Panel crashes on Qt6 / Houdini 21.
* [fix] Styling; ftrack dialogs are now styled on Houdini < 21 (PySide2/Qt5). The bundled ftrack-qt-style resource imported PySide6 unconditionally, which failed on PySide2 Houdini and left dialogs with Houdini's default style; the import now falls back to PySide2.
* [changed] Build; migrated the build system and formatting to uv/ruff.

## v24.11.0
2024-11-21

* [fix] Plugin; Framerange is now set correctly at startup.
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
