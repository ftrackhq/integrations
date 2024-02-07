# ftrack RV integration release Notes

## Upcoming
YYYY-mm-dd

* [changed] Aligned with Connect 3 integrated launcher and improved hook.
* [fixed] Rv does not play Entity selections.
* [fixed] Log initialization breaks due to utf8 conversion.
* [fixed] Rv breaks not being able to parse tempdata.
* [fixed] Panel size too small at startup.
* [changed] Use poetry as build system.

## v5.0
2021-09-07

* [changed] Port to python 3 and PySide2.
* [changed] Refactor to support RV 20XX.
* [fixed] Failed to jump to index error.
* [warning] From this version the support for ftrack-connect 1.X is dropped, and only ftrack-conenct 2.0 will be supported up to the integration EOL.

## v4.0
2020-01-14

* [changed] Moved from Qt Webkit to Qt WebEngine for Qt 5.12 / RV 7.5+.
* [changed] Exposing dependencies folder to resultant build folder.
* [changed] Build resultant folder renamed with the plugin name + version.
* [changed] ftrack-location-compatibility version updated to 0.3.3.
* [changed] Pip compatibility for version 19.3.0 or higher.

## v3.7
2017-11-17

* [fixed] Fail gracefully if a single asset version fails to load.

## v3.6
2017-06-28

* [fixed] Unable to add notes with annotations.
* [fixed] Plugin outputs error if installation location is not found for RV under Linux.
* [fixed] The action is registered twice in ftrack connect.

## v3.5
2017-05-30

* [fixed] RV crashes when loading a previously loaded version for the second time.

## v3.4
2017-05-17

* [new] Added installation instructions.
* [fixed] New versions of RV are not found in their default
