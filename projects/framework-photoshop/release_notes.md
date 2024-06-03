# ftrack Framework Photoshop integration release Notes

## upcoming

* [feat] Added support for bootstrap tools run after Photoshop connection established.


## 24.5.0
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
