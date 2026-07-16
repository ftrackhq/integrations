# ftrack Connect release Notes

## v26.7.0
2026-07-15

* [new] macOS; Provide separate Intel (x86_64) and Apple Silicon (arm64) installers. DMG filenames now carry an architecture suffix (ftrack_connect-<version>-macOS-x86_64.dmg / -arm64.dmg).
* [changed] Performance; Add query projections to startup queries (project tree, recent actions, storage scenario check), eliminating per-entity N+1 server requests.
* [fix] Plugin manager; Populate the plugin list on the main Qt thread and fetch GitHub releases through a background worker, preventing instability; plugins incompatible with the current platform are now flagged with a warning.
* [fix] Session; Close the previous API session before creating a new one when the storage scenario is configured, preventing double session initialization.
* [fix] Plugin manager; Compare plugin versions using PEP 440 parsing instead of string comparison when resolving duplicate plugins.
* [fix] Fix crash on restart when Connect is launched with --allow-multiple.
* [fix] About; Widget plugin debug information is correctly included again.
* [fix] Hooks; Open component directory hook updated to use new event source.host for discovery and launch.
* [fix] Launcher; On macOS, deliver injected launch arguments through 'open --args' instead of as trailing document paths, preventing a second, wrong-version DCC instance from being started via LaunchServices when arguments are injected.
* [fix] Launcher; When Connect runs frozen (installed), strip its own bundled Qt paths (QT_PLUGIN_PATH, QT_QPA_PLATFORM_PLUGIN_PATH, QML/QML2_IMPORT_PATH, PATH and the loader library paths) from the environment handed to launched applications, so a DCC no longer loads Connect's Qt plugins/libraries built against a different Qt minor (which produced "incompatible Qt library" warnings, crashes and missing menus/dialogs). Studio-set entries are preserved and take precedence.
* [changed] Launcher; Launched applications no longer inherit Connect's bundled Qt plugins (strictly correct behaviour). A studio that needs specific Qt environment variables for a launched DCC must set them via the launch config's environment_variables block or an integration hook; these are applied after the scrub and take precedence.
* [fix] Integrations; Preserve backward compatibility for older integration plugins by serializing the launched application version as a string that still exposes a LooseVersion-style .version attribute, so launch hooks reading application['version'].version[0] keep working.
* [changed] Build; Migrate build system from Poetry to uv and code formatting from black to ruff.
* [changed] Build; Update Python runtime to 3.13.
* [changed] Dependencies; ftrack-python-api updated to 3.x, ftrack-utils, ftrack-framework-core and ftrack-constants to 4.x, certifi and urllib3 updated.

## v25.11.0rc1
2025-11-27

* [fix] Publisher; Improve image sequence padding detection (clique).
* [changed] Build; macOS builds now produced on macOS 15 runners; Linux build steps locked to Ubuntu 22.04.

## v24.11.1
2024-12-12

* [fix] Provide proper fallback when icon is not found.

## v24.11.0
2024-11-21

* [changed] Login; Add login unique identifier when login with Connect; ftrack-connect-<local_user>@<mac_hex>
* [changed] Dependencies; Poetry update.
* [changed] Move deprecated HighDPI settings into PySide2 specific codepath.
* [fix] Fix ctrl+c interrupt behaviour when launching connect through the commandline. It will now properly exit the application.
* [fix] Remove obsolete pkg_resources import which lead to errors when launching through the commandline
* [changed] Add debug logs on item_selector and asset_selector widgets to debug publisher.

## v24.9.0

* [changed] Ftrack libraries updated to ^3.0.0.
* [fix] Add xcb-util-cursor for Rocky linux builds and ensure PySide6 is bundled.


## v24.7.0
2024-07-17

* [fix] Add full ftrack_api and ftrack_Action_handler modules on connect package.


## v24.6.0
2024-06-04

* [fix] Support uncompress files with internal top level directory.


## v24.5.3
2024-05-21

* [fix] Fix open_component_directory.py hook not discovering correctly.


## v24.5.2
2024-05-14

* [new] Ability to set the default URL for downloading releases from Github in the plugin manager, by setting the environment variable FTRACK_CONNECT_GITHUB_RELEASES_URL. Also supports disabling fetch by setting it to 'none'.
* [new] Possibility to disable the plugin manager by setting environment variable FTRACK_CONNECT_DISABLE_PLUGIN_MANAGER to true.


## v24.5.1
2024-05-13

* [fix] Fix issue with connect login not working on Windows.
* [changed] Prevent additional icon for standalone process to appear on windows.


## v24.5.0
2024-05-07

* [changed] Add certifies just when running from installer.
* [changed] Make sure Windows executable is code signed.
* [changed] Connect installer removed, now using a script to call the ftrack-app-installer library to package connect and codesign it on all platforms.
* [changed] New versioning system matching all backlight products.
* [changed] Allow non versioned connect plugins, supporting legacy actions naming convention.
* [changed] Fixed overlay widget bugs.
* [new] PySide6 support;
* [new] PySide2 support.
* [changed] Removed ftrack_connect.qt module.
* [changed] Removed Qt.py dependency.


## v3.0.0
2024-04-02

* [fix] If a launch config isn't valid, it will now be ignored so Connect doesn't crash.
* [fix] Optimized and properly using version parsing when sorting Github releases.
* [new] Toggle pre-releases in Plugin manager
* [changed] Introduced FTRACK_CONNECT_EXTENSIONS_PATH, read by Connect to resolve launch configurations.
* [new] Proper support for launch config extensions, merging configs based on the order they appear in FTRACK_CONNECT_EXTENSIONS_PATH.
* [new] Now uses framework-core (ftrack_framework_core) library as a dependency.
* [changed] Re-structure utils and move general ones to ftrack-utils library.
* [changed] config.json file renamed to credentials.json
* [changed] Plugin manager; Drag-n-drop of a plugin ZIP overrides any existing plugins in plugin list.
* [changed] Consolidated plugin management: FTRACK_CONNECT_PLUGIN_PATH now overrides the local plugin directory instead of merging. Plugins already in plugin path are not added twice.
* [changed] Plugin manager now considers plugins in FTRACK_CONNECT_PLUGIN_PATH.
* [changed] Improved about window - More information to include debug information from widget plugins.
* [changed] Do not prevent Connect from launching if there is no system tray.
* [changed] Support for detecting and warning about integrations requiring Rosetta on Apple Silicon. 
* [changed] Ported and integrated the ftrack-application-launcher module and switched over to YAML configuration support.
* [changed] Support for environment variables in launcher configs.
* [changed] Ported and integrated the ftrack-connect-action-launcher-widget.
* [changed] Made it read from Github releases instead of AWS plugin space.
* [changed] Ported and integrated the ftrack-connect-plugin-manager
* [new] Support for new extension based integrations, utilising the ftrack-utils library.


## v2.1.1
2023-04-27

* [fixed] Plugins. Limit packaging to prevent crashes on unexpected content in Connect plugin folder.

## v2.1.0
2023-04-05

* [changed] Plugins. Install all plugins on first launch.
* [changed] Docs. Update CONTRIBUTING.md to include release notes.
* [fixed] UI. Application crash on Windows 8.1.
* [fixed] API. Ensure all plugin paths are unique.

## v2.0.1
2022-09-01

* [fixed] UX. Action icons are being cut in task launcher.
* [fixed] UX. Icons fonts are not correctly loaded during storage setup.

## v2.0.0
2022-07-07

* [fixed] UX. User's tasks include inactive projects.
* [changed] Tray. Windows and Linux use color icon in system tray.
* [fixed] Style. Variant are highlighted black on light style.
* [fixed] Linux. Application shortcut points to wrong executable.
* [fixed] UX. Path with unicode are not rendered spaced correctly.

## v2.0.0-rc-6
2022-06-01

* [changed] Login. Provide link to get back on logging in through instance address.
* [changed] Style. Remove play button from action launch and review style.
* [fixed] UX. Interface expand on long context paths.
* [fixed] Publisher. Add missing icons and set correct state for drop zone on folders.
* [fixed] Publisher. Latest published assets are not always refreshing.
* [changed] Style. Review Dialogs styles.
* [changed] Style. Review style and icons.
* [new] SystemTray, API. Allow connect to restart.
* [changed] Plugins. Remove publisher and launcher from connect codebase. Documentation can be found in:
        Publisher documentation
        Launcher documentation
* [changed] Codestyle. Run black pass with flags : black --skip-string-normalization -l 79 . on Codebase.

## v2.0.0-rc-5
2022-03-25

* [fixed] Actions. Random crashes on discovering on null context.
* [new] Module. Provide ftrak_connect.qt module to abstract imported Qt modules.
* [changed] Events. Sending of usage_events can now be batched.
* [changed] About, Linux. Linux Desktop entry respect packaged or virtual environment paths.
* [changed] UX. Add new icons set for Connect.
* [changed] UX. Connect color theme respect system theme.

## v2.0.0-rc-4
2022-01-15

* [changed] UX. Assigned tasks are refreshed on cancel.
* [changed] API. User's plugin folder is created at startup time.
* [changed] UX. Context selection is changed to a list of assigned tasks.
* [new] UX. Indicator during discovery of actions.
* [new] API. Provide ConnectWidget Plugin with custom name attribute to render.
* [new] API. Improve ConnectWidget error logging.
* [new] API. Emit usage data for Connect session duration along version and os type.
* [fixed] API. Storage scenario help points to dead link.
* [changed] UX. Provide placeholder text in context selectors.
* [fixed] UX. Menubar icon smaller on Mac.
* [changed] UX. Update icon set to use font icons (material/ftrack icons) to ensure full hidpi support.
* [changed] UX. Consolidate font using Roboto.
* [changed] API. Remove ftrack_connect.session utility class, and shared_session usage.
* [changed] Logging. Improve logging readability.
* [new] API. Restore ftrack_connect.application module to provide environment variable helper methods.

## v2.0.0-rc-3
2021-09-23

* [changed] Setup. Use latest api release version.
* [fixed] API. Cannot publish after a failed publish, and need to restart connect.

## v2.0.0-rc-2
2021-07-13

* [changed] Documentation. Update with latest images.

## v2.0.0-rc-1
2021-06-18

* [changed] UI. Integrations are returned sorted by name in About page.
* [changed] ConnectWidgetPlugin. Improve error handling.

## v2.0.0-beta-4
2021-06-07

* [new] UI. Allow connect to be always on top of other windows.

## v2.0.0-beta-3
2021-05-21

* [changed] API. Review ConnectWidgetPlugin base classes.

## v2.0.0-beta-2
2021-03-18

* [new] Ui. Provide ability to extend connect through ConnectWidgets plugins.

## v2.0.0-beta-1
2021-03-11

* [changed] Ui. Move to Pyside2.
* [changed] API. Remove ftrack-python-legacy-api dependency and dependent code.
* [new] Ui. Replace QtExt with Qt.py module.
* [changed] Changed. Move connector integration codebase to separate repository.
* [new] Setup. Use setuptool_scm to infer version.
* [fixed] Application launcher. Standalone installation does not correctly inject dependencies at application startup.
* [changed] Code. Port code to python3.

## v1.1.10
2021-05-21

* [fixed] Doc. Provide requirement file for RTD builds.

## v1.1.9
2021-03-11

* [fixed] Open_directory. Opening component breaks on cloud paths.
* [fixed] Application launcher. Standalone installation does not correctly inject dependencies at application startup.

## v1.1.8
2020-01-21

* [new] Internal. Added a lockfile mechanism so Connect will exit if another instance is already running. Users can pass a command-line flag, -a or --allow-multiple, to skip this check.

## v1.1.7
2019-03-08

* [new] Ui. Added button in About dialog to create a Linux desktop entry file to make Connect appear in the applications menu.

## v1.1.6
2018-10-8

* [changed] Ui. Update icons and style.
* [fixed] Internal. Util.open_directory fails on Windows when path includes spaces.

## v1.1.5
2018-09-13

* [fixed] Logging. Logger breaks with non ascii path.
* [changed] Logging. Improve logging configuration.
* [fixed] Ui. Application versions are not correctly sorted.

## v1.1.4
2018-04-27

* [fixed] Import asset. Import Asset breaks checking for asset in remote locations.
* [changed] Crew. Remove Crew widget chat and notifications.
* [changed] Ui. Added feature to hide the ftrack-connect UI on startup. This is done with the flag "--silent" or "-s".

## v1.1.3
2018-02-02

* [fixed] Plugins. ftrack.connect.plugin.debug-information only published for the legacy api.

## v1.1.2
2017-12-01

* [fixed] Documentation. Release notes page is not formatted correct.

## v1.1.1
2017-11-16

* [fixed] API. Error when publishing in connect with non-task context.

## v1.1.0
2017-09-12

* [changed] Import asset. Component location picker now defaults to location where the component exists. If a component exists in more than one location, the priority order determines the default location.
* [fixed] Info dialog, Tasks dialog. Info and Tasks dialogs are not compatible with recent versions of Qt.
* [fixed] API. All widgets are not compatible with recent versions of Qt.

## v1.0.1
2017-07-11

* [fixed] Asset manager. Cannot change version of versions with a sequence component.

## v1.0.0
2017-07-07

* [fixed] API. Errors in hooks are shown as event hub errors.
* [fixed] Ui, Asset manager. Asset manager fails to open in some rare cases.
* [fixed] API. Application search on disk does not follow symlinks.
* [changed] Events, API. The ftrack.connect.application.launch event is now also emitted through the new api. The event allows you to modify the command and/or environment of applications before they are launched.
* [changed] API. Changed Connector based plugins to use the new API to publish assets.
* [fixed] Ui, Import asset. Import asset dialog errors when a version has no user.
* [changed] API. Changed from using legacy API locations to using locations from the ftrack-python-api. Make sure to read the migration notes before upgrading.
* [fixed] Internal. Fixed occasional X11 related crashes when launching actions on Linux.
* [changed] Publish. The new api and locations are used
