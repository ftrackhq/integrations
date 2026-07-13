/**
 * Harmony ftrack integration - scene-opened hook. [ftrack]
 *
 * Harmony rebuilds the menu bar whenever a scene is opened (File > Open,
 * the ftrack Open tool, or close-and-reopen), dropping script-added
 * items. This hook re-registers the ftrack menu entries after each
 * scene open.
 *
 * A user-level TB_sceneOpened OVERRIDES Harmony's default one, so we
 * CHAIN: include the default, keep a reference and call it before our
 * own logic - never clobber it (even though the current default only
 * prints). The default lives at
 * specialFolders.resource/scripts/TB_sceneOpened.js.
 *
 * The launcher list is read from a JSON string persisted on the shared
 * QCoreApplication by configure.js (arrays read back across script
 * engines are lossy copies; a string round-trips).
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
    ftrackReregisterMenuHook();
    ftrackReregisterServerHook();
};

/**
 * Re-stand-up the ftrack TCP server after Harmony tore down the Qt Script
 * engine (and the server) on this scene open. Harmony does NOT re-invoke
 * the package configure(), so we re-include configure.js from the package
 * folder (absolute path supplied by the Connect launch hook via
 * FTRACK_HARMONY_PACKAGE_PATH) and call its ftrackEnsureIntegration().
 * Setting __packageFolder__ first makes configure.js pull in its own
 * utilities (utils.js/harmony_commands.js). Once the server is back the
 * standalone process reconnects and rebuilds the menu and toolbar.
 */
function ftrackReregisterServerHook() {
    try {
        var packageRoot = System.getenv("FTRACK_HARMONY_PACKAGE_PATH");
        if (!packageRoot) {
            MessageLog.trace(
                "[ftrack] FTRACK_HARMONY_PACKAGE_PATH not set - cannot "
                + "re-establish TCP server after scene open."
            );
            return;
        }
        __packageFolder__ = packageRoot;
        include(packageRoot + "/ftrack/configure.js");
        if (typeof ftrackEnsureIntegration === "function") {
            ftrackEnsureIntegration();
            MessageLog.trace(
                "[ftrack] Re-established TCP server after scene open."
            );
        } else {
            MessageLog.trace(
                "[ftrack] ftrackEnsureIntegration undefined after include."
            );
        }
    } catch (err) {
        MessageLog.trace("[ftrack] server re-registration failed: " + err);
    }
}

/**
 * Re-register the ftrack menu entries from the persisted launcher list.
 */
function ftrackReregisterMenuHook() {
    try {
        var launchers = JSON.parse(
            QCoreApplication.instance().ftrack_launchers_json || "[]"
        );
        for (var idx = 0; idx < launchers.length; idx++) {
            ScriptManager.addMenuItem({
                targetMenuId: "File",
                id: "ftrackMenu" + launchers[idx]["name"] + "ID",
                icon: "ftrack.png",
                text: "ftrack " + launchers[idx]["label"],
                action:
                    "launch_" + launchers[idx]["name"] + " in ./configure.js"
            });
        }
    } catch (err) {
        MessageLog.trace("[ftrack] menu re-registration failed: " + err);
    }
}
