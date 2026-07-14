# ftrack Framework Harmony integration release Notes


## v26.7.0rc1

* [feat] The ftrack menu, toolbar and shortcut stay present and clickable across scene switches (File > Open, File > New, close-and-reopen, the ftrack Open tool). The standalone process is the TCP server and Harmony the client that dials out; Harmony tears down its Qt Script engine (and the client socket) on every scene switch but the external server outlives it, so Harmony reconnects and the server re-sends its tool list to rebuild the menu, toolbar and shortcut (none of them survive a scene switch). Deployed TB_sceneOpened and TB_sceneCreated hooks re-include configure.js, re-register the menu entries synchronously (so the menu is back immediately) and reconnect to restore the RPC channel; each chains Harmony's default callback (the default TB_sceneCreated builds the new scene), so the standard behaviour is preserved.
* [feat] Publish a scene snapshot (the Harmony scene folder, zipped) as a `snapshot` component alongside the render.
* [feat] The scene snapshot zip is named after the scene (`<SceneName>.zip`).
* [feat] Add a scene opener that opens a published snapshot in the running session via `scene.closeSceneAndOpenOffline`.
* [feat] Group the ftrack tools as adjacent entries at the end of the File menu (Open, then Publish) plus a dedicated "ftrack" toolbar with one button per tool.
* [fix] The standalone process binds its RPC server port immediately at launch and listens for Harmony's whole lifetime, so there is no connect race: Harmony (the client) connects as soon as a scene is open and reconnects on every subsequent scene switch.
* [fix] Shut the standalone process down when Harmony exits, via a process watchdog that polls the Harmony PID. A scene switch (TCP disconnect) no longer terminates it — Harmony drops the socket on every scene switch and simply reconnects to the still-listening server.
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

