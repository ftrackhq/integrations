/**
 * Harmony ftrack integration - scene-created hook. [ftrack]
 *
 * Harmony tears down the Qt Script engine - and this engine's socket to
 * the ftrack RPC server - whenever a scene is created (File > New), and
 * rebuilds the menu bar (dropping script-added items). This hook
 * reconnects the integration to the standalone process' RPC server after
 * a new scene is created; on reconnect the standalone re-sends its
 * context data, which rebuilds the ftrack menu (the toolbar and shortcut
 * persist).
 *
 * A user-level TB_sceneCreated OVERRIDES Harmony's default one (only one
 * runs), and the default does essential work (60 frames, Composite/
 * Display/Write nodes, a drawing column). So we CHAIN: include the
 * default, keep a reference, and call it before our own logic - never
 * clobber it. The default lives at
 * specialFolders.resource/scripts/TB_sceneCreated.js.
 *
 * Deployed to the user scripts root by the ftrack Connect plugin (see
 * connect-plugin/hook/discover_ftrack_framework_harmony.py). The
 * "[ftrack]" marker above identifies the file as ours so the deploy
 * never overwrites a studio's own TB_sceneCreated.js.
 *
 * Copyright (c) 2026 ftrack
 */

// Chain Harmony's default TB_sceneCreated (essential new-scene setup).
// Use assignment (not a function declaration) for our wrapper so it is
// not hoisted above the include that defines the default.
var ftrackDefaultSceneCreated = null;
try {
    include(specialFolders.resource + "/scripts/TB_sceneCreated.js");
    ftrackDefaultSceneCreated = TB_sceneCreated;
} catch (err) {
    MessageLog.trace(
        "[ftrack] Could not load default TB_sceneCreated: " + err
    );
}

TB_sceneCreated = function() {
    if (typeof ftrackDefaultSceneCreated === "function") {
        try {
            ftrackDefaultSceneCreated();
        } catch (err) {
            MessageLog.trace(
                "[ftrack] default TB_sceneCreated failed: " + err
            );
        }
    } else {
        MessageLog.trace(
            "[ftrack] default TB_sceneCreated unavailable - new scene "
            + "may lack the default setup."
        );
    }
    ftrackReconnectHook();
};

/**
 * Reconnect the ftrack integration to the standalone process' RPC server
 * after Harmony tore down the Qt Script engine (and this engine's socket)
 * on this scene creation. Harmony does NOT re-invoke the package
 * configure(), so we re-include configure.js from the package folder
 * (absolute path supplied by the Connect launch hook via
 * FTRACK_HARMONY_PACKAGE_PATH) and call its ftrackConnectIntegration().
 * Setting __packageFolder__ first makes configure.js pull in its own
 * utilities (utils.js/harmony_commands.js).
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
                + "reconnect the ftrack integration after scene create."
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
                "[ftrack] Reconnected the ftrack integration after scene create."
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
