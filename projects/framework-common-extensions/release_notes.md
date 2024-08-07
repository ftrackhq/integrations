# ftrack Framework Common Extensions release Notes

## Upcoming

* [fixed] StandardPublisherDialog; Fix bug were _accordion_widgets_registry wasn't initialized if no tool_config available.
* [fixed] StandardOpenerDialog, StandardPublisherDialog; Fix bug were dialog creation crashed if not tool configs. Also disabled run button.
* [changed] RenameFileExporterPlugin; Accept folder as destination.
* [required] Add clique 1.6.1 as dependency.
* [changed] FileBrowserCollectorWidget emit signal when path changed.
* [fix] StandardPublisherDialog; Support enable and disable components.
* [new] Exported paths validator to support image sequences.
* [new] PySide6 support.
* [new] PySide2 support.
* [changed] Removed Qt.py dependency.
* [changed] Standard opener and publisher are using the stack widget to show overlay widget from progress widget and options widget.
* [changed] Remove setObjectName when not necessary on qtWidgets. Using properties to set the style instead.
* [changed] Asset version selectors; show label on empty asset list.
* [changed] Publisher dialog only query assets linked to the task.
* [changed] Opener dialog has checkbox to query assets from AssetBuild
* [new] Publisher suggest new asset name based on task type.
* [changed] Add windows specific titles on standard opener dialog and standard publisher dialog.
* [changed] Added labels to publisher asset selector and publisher, aligned margins.
* [new] Initial release.
