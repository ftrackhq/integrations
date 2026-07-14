/**
 * Harmony ftrack integration - scene-opened hook. [ftrack]
 *
 * Harmony tears down the Qt Script engine - and this engine's socket to
 * the ftrack RPC server - whenever a scene is opened (File > Open, the
 * ftrack Open tool, or close-and-reopen), and rebuilds the menu bar
 * (dropping script-added items). This hook reconnects the integration to
 * the standalone process' RPC server after each scene open; on reconnect
 * the standalone re-sends its context data, which rebuilds the ftrack
 * menu (the toolbar and shortcut persist).
 *
 * A user-level TB_sceneOpened OVERRIDES Harmony's default one, so we
 * CHAIN: include the default, keep a reference and call it before our
 * own logic - never clobber it (even though the current default only
 * prints). The default lives at
 * specialFolders.resource/scripts/TB_sceneOpened.js.
 *
 * Deployed to the user scripts root by the ftrack Connect plugin (see
 * connect-plugin/hook/discover_ftrack_framework_harmony.py). The
 * "[ftrack]" marker above identifies the file as ours so the deploy
 * never overwrites a studio's own TB_sceneOpened.js.
 *
 * Copyright (c) 2026 ftrack
 */

// Chain Harmony's default TB_sceneOpened. Use assignment (not a
// function declaration) for our wrapper so it is not hoisted above the
// include that defines the default.
var ftrackDefaultSceneOpened = null;
try {
    include(specialFolders.resource + "/scripts/TB_sceneOpened.js");
    ftrackDefaultSceneOpened = TB_sceneOpened;
} catch (err) {
    MessageLog.trace(
        "[ftrack] Could not load default TB_sceneOpened: " + err
    );
}

TB_sceneOpened = function() {
    if (typeof ftrackDefaultSceneOpened === "function") {
        try {
            ftrackDefaultSceneOpened();
        } catch (err) {
            MessageLog.trace(
                "[ftrack] default TB_sceneOpened failed: " + err
            );
        }
    } else {
        MessageLog.trace(
            "[ftrack] default TB_sceneOpened unavailable - scene may lack "
            + "the default setup."
        );
    }
    ftrackReconnectHook();
};

/**
 * Reconnect the ftrack integration to the standalone process' RPC server
 * after Harmony tore down the Qt Script engine (and this engine's socket)
 * on this scene open. Harmony does NOT re-invoke the package configure(),
 * so we re-include configure.js from the package folder (absolute path
 * supplied by the Connect launch hook via FTRACK_HARMONY_PACKAGE_PATH) and
 * call its ftrackConnectIntegration(). Setting __packageFolder__ first
 * makes configure.js pull in its own utilities
 * (utils.js/harmony_commands.js).
 *
 * The menu entries are re-registered synchronously from the persisted
 * launcher list (ftrackRebuildMenus) so the ftrack menu is back
 * immediately, without waiting for the async reconnect + context-data
 * round trip. The reconnect then restores the RPC channel (so the menu
 * actions work) and the standalone re-sends its context data, which
 * rebuilds the menu once more (idempotent, stable ids); the toolbar and
 * shortcut persist across scene switches.
 */
function ftrackReconnectHook() {
    try {
        var packageRoot = System.getenv("FTRACK_HARMONY_PACKAGE_PATH");
        if (!packageRoot) {
            MessageLog.trace(
                "[ftrack] FTRACK_HARMONY_PACKAGE_PATH not set - cannot "
                + "reconnect the ftrack integration after scene open."
            );
            return;
        }
        __packageFolder__ = packageRoot;
        include(packageRoot + "/ftrack/configure.js");
        // Restore the menu items synchronously first (does not depend on
        // the network); reconnect then makes them functional again.
        if (typeof ftrackRebuildMenus === "function") {
            ftrackRebuildMenus();
        }
        if (typeof ftrackConnectIntegration === "function") {
            ftrackConnectIntegration();
            MessageLog.trace(
                "[ftrack] Reconnected the ftrack integration after scene open."
            );
        } else {
            MessageLog.trace(
                "[ftrack] ftrackConnectIntegration undefined after include."
            );
        }
    } catch (err) {
        MessageLog.trace("[ftrack] reconnect failed: " + err);
    }
}
