# ftrack Framework Harmony integration release Notes


## v26.7.0rc1

* [feat] Re-register the ftrack menu entries after a scene is opened (via a deployed TB_sceneOpened hook), so they persist across File > Open, close-and-reopen and the ftrack Open tool. Creating a brand-new scene (File > New) does not re-register them; open any scene to restore them.
* [feat] Publish a scene snapshot (the Harmony scene folder, zipped) as a `snapshot` component alongside the render.
* [feat] The scene snapshot zip is named after the scene (`<SceneName>.zip`).
* [feat] Add a scene opener that opens a published snapshot in the running session via `scene.closeSceneAndOpenOffline`.
* [feat] Group the ftrack tools as adjacent entries at the end of the File menu (Open, then Publish) plus a dedicated "ftrack" toolbar with one button per tool.
* [fix] The standalone process now waits indefinitely for Harmony to open a scene (package scripts only start with the scene UI); previously it gave up after 2 minutes, leaving the ftrack menu missing for the session. The process watchdog still terminates it when Harmony quits.
* [fix] Shut the standalone process down when Harmony exits: a process watchdog plus a hard-terminate on TCP disconnect (the previous `sys.exit` was swallowed by the Qt event loop, leaving the helper process running).
* [fix] Keep the standalone process alive when a dialog is closed (`setQuitOnLastWindowClosed(False)`); previously closing the publisher quit the process and the ftrack menu only opened a dialog once.
* [fix] Image sequence export no longer fails with `[Errno 17] File exists`; the sequence exporter now requests a temporary directory instead of a temporary file.
* [fix] Fix standalone integration crash on Python 3.13 by rebuilding against the current ftrack libraries (`registry.scan_extensions` used the removed `importlib` `find_module` API).
* [fix] Robust `FTRACK_INTEGRATION_LISTEN_PORT` handling and clean PySide2/PySide6 `exec` fallback in the standalone bootstrap.
* [fix] Connect hook is importable from the source tree (version fallback) and can deploy the JS package from an explicit bootstrap path.
* [feat] Automated launch/bootstrap tests via the `dcc-test-harness` library, hooking into the Connect launcher 1:1 (tier 1: JS package + menu + RPC; tier 2: full standalone-process bootstrap).
* [doc] README aligned with the other projects and documents the two-process architecture, supported Harmony versions (22–27) and Toon Boom API validity.
* [ci] Enable the Connect-plugin CI build for framework-harmony.
* Note: opener/loader/asset-manager workflows remain deferred. A migration of the DCC command surface from JS-eval RPC to Toon Boom's external Python API (Harmony 24+) is tracked as a future spike; the current JS/TCP interaction model is unchanged.


## v24.6.0rc1

* [feat] Initial release. Not building on CI; still needs an update of all libraries.

