/**
 * Harmony ftrack integration - scene-created hook. [ftrack]
 *
 * Harmony rebuilds the menu bar whenever a scene is created (File > New),
 * dropping script-added items. This hook re-registers the ftrack menu
 * entries after a new scene is created.
 *
 * A user-level TB_sceneCreated OVERRIDES Harmony's default one (only one
 * runs), and the default does essential work (60 frames, Composite/
 * Display/Write nodes, a drawing column). So we CHAIN: include the
 * default, keep a reference, and call it before our own logic - never
 * clobber it. The default lives at
 * specialFolders.resource/scripts/TB_sceneCreated.js.
 *
 * The launcher list is read from a JSON string persisted on the shared
 * QCoreApplication by configure.js (arrays read back across script
 * engines are lossy copies; a string round-trips).
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
    ftrackReregisterMenuHook();
};

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
