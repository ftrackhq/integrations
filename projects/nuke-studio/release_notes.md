# ftrack Nuke Studio integration release Notes

## v24.2.0
2024-02-13

* [changed] Aligned with Connect 3 integrated launcher and improved hook.
* [changed] Use poetry as build system.

## v2.5.0
2021-09-06

* [changed] Discovery.


## v2.4.1
2020-09-15

* [added] Startup error related to location setup are now visually reported.
* [fixed] Discovery does break on non context entities.

## v2.4.0
2020-06-17

* [fixed] Rebuild track from exported episodes does not work.
* [changed] Ensure shot export path is consistent with the location structure generated.
* [new] Add 'Ftrack Copy Exporter' for publish file or sequence to ftrack without transcoding.
* [fixed] Tokens are not always parsed correctly.
* [changed] Ensure shot output path normalized when replacing shot name.
* [changed] Replace fixed version with automatic versioning from git repository.
* [fixed] Reviewable export audio breaks on earlier Nuke Studio versions (version < 12.1).
* [fixed] Reviewable Task break when including audio.

## v2.3.0
2020-04-23

* [fixed] Custom start frame are not consistently output in frame sequence.
* [changed] Lock OTIO dependency version to last python only.
* [fixed] Sequences rendered with Nuke Studio cannot be imported in nuke.
* [fixed] ImageSequences are rendered as FileComponent.
* [fixed] Thumbnail generation breaks when exporting just nuke scripts.

## v2.2.5
2020-03-12

* [fixed] Thumbnail generation breaks when setting custom start frame.

## v2.2.4
2020-01-21

* [changed] Pip compatibility for version 19.3.0 or higher
* [added] Mark ftrack.perforce-location as non compatible.
* [fixed] Replace pyqt with qt.py

## v2.2.3
2019-10-21

* [fixed] Improve render task deduplication logic.
* [fixed] Integration fails to start on nuke >= 12.
* [fixed] Thumbnail frame is now generated from the mid frame of the exported clip.

## v2.2.2
2019-07-10

* [changed] Replace QtExt module with QtPy.

## v2.2.1
2019-05-22

* [fixed] Tasks are marked as duplicated if the same clip name is present on multiple tracks.
* [fixed] Tasks generate empty unwanted components.
* [changed] Replace simple EDL export with OpenTimelineIO edl export.
* [new] Thumbnails are published also to parent entity.

## v2.2.0
2019-03-08

* [new] Extend context template to support episodes.
* [changed] Application requires a project to start and project selection from export is now disabled.

## v2.1.3
2019-02-21

* [fixed] Edl Exporter generates empty components.
* [new] Better error handling to log.

## v2.1.2
2019-01-17

* [fixed] Due to application api changes, the plugin does not work in Nuke Studio/Hiero versions >= 11.3v1.

## v2.1.1
2019-01-11

* [fixed] Presets are not properly restored between sessions.
* [fixed] Components are not collected under one single asset.

## v2.1.0
2018-12-17

* [new] Support tokens resolution in component names.
* [new] Support multi track export.
* [fixed] Hiero under windows does not load templates.

## v2.0.1
2018-11-12

* [fixed] Error when trying to validate duplicated components.

## v2.0.0
2018-10-08

* [new] Complete re write of the integration as standalone plugin.

## v1.1.2
2017-04-27

* [fixed] Nuke Studio 11.1 crashes with ftrack integration.

## v1.1.0

2017-09-12

* [fixed] Nuke 11 not supported.

## v1.0.0
2017-07-07

* [fixed] Occasional errors when running processors.
* [fixed] Show an error dialog if the img asset type does not exist in the server.
* [new] Remove dependencies on the ftrack legacy API where possible.
* [new] Add new event to allow modification of the template output structure.

## v0.2.7
2017-01-11

* [fixed] Cannot set custom attributes when used in combination with new api and ftrack server version.

## v0.2.6
2016-12-01

* [changed] Switched to require ftrack-python-api > 1.0.0.

## v0.2.5
2016-08-03

* [fixed] Processors fail in NukeStudio 10.0v3 and later for single-file track items.

## v0.2.4
2016-06-07

* [fixed] Schema selection is not in sync with the selected exiting project.

## v0.2.3
2016-05-02

* [fixed] Plugin doesn't work with Nuke Studio 10.0v1 beta.

## v0.2.2
2016-04-04

* [fixed] Handles are not treated correctly when publishing through processors.

## v0.2.1
2016-03-14

* [changed] Track item is passed as application_object when discovering processors.
* [fixed] Fix issue where a project cannot be created or updated from the Create dialog.
* [fixed] Meta data on project is overwritten when an existing project is updated.

## v0.2.0
2015-11-10

* [new] Introduced Context templates to simplify configuration of project structure on export.

## v0.1.4
2015-10-16

* [changed] Default tag expressions now check for either the previous syntax or as-is naming to support a wider variety of use cases out of the box.
* [changed] Improved error messages shown when tag expression does not match.

## v0.1.3
2015-10-01

* [changed] Propagate thumbnails to tasks on export by default.
* [changed] Publish and Proxy processors disabled as default.
* [changed] Store reference to outermost ftrack entity in hierarchy when exporting track items.
* [fixed] Info panel not updating if track item has effect track.

## v0.1.2
2015-09-22

* [fixed] Processors not working correct on Windows.
* [fixed] Incomplete version number displayed for Nuke Studio application when discovered.
* [fixed] Changes to context tags hook not being respected.
* [changed] Read default export values for fps and resolution from the project settings.

## v0.1.1
2015-09-10

* [fixed] Dropping several tags of same type causes export to fail.
* [fixed] Segmentation fault when closing down Nuke Studio with plugin loaded.
* [changed] Updated default export values for fps, resolution and handles.
* [fixed] In and out points not calculated correctly when when offset is used on source clip.

## v0.1.0
2015-09-08

* [new] Initial release of ftrack connect Nuke

