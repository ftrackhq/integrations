/**
 * Harmony ftrack integration - scene-opened hook. [ftrack]
 *
 * Harmony rebuilds the menu bar whenever a scene is opened (File > Open,
 * the ftrack Open tool, or close-and-reopen), dropping script-added
 * items. This hook runs after each scene open and re-registers the
 * ftrack menu entries.
 *
 * Runs in its own script engine, so it depends only on things reachable
 * across engines: the launcher list is read from a JSON string stored on
 * the shared QCoreApplication by configure.js (arrays/objects read back
 * from a script object across engines are lossy copies - a string round
 * trips), and ScriptManager is a global.
 *
 * Deployed to the user scripts root by the ftrack Connect plugin (see
 * connect-plugin/hook/discover_ftrack_framework_harmony.py). The
 * "[ftrack]" marker above identifies the file as ours so the deploy
 * never overwrites a studio's own TB_sceneOpened.js.
 *
 * Copyright (c) 2026 ftrack
 */

function ftrackReregisterMenu() {
    var launchers = [];
    try {
        launchers = JSON.parse(
            QCoreApplication.instance().ftrack_launchers_json || "[]"
        );
    } catch (err) {
        MessageLog.trace("[ftrack] Could not read launchers: " + err);
        return;
    }
    for (var idx = 0; idx < launchers.length; idx++) {
        var launcher = launchers[idx];
        ScriptManager.addMenuItem({
            targetMenuId: "File",
            id: "ftrackMenu" + launcher["name"] + "ID",
            icon: "ftrack.png",
            text: "ftrack " + launcher["label"],
            action: "launch_" + launcher["name"] + " in ./configure.js"
        });
    }
}

try {
    ftrackReregisterMenu();
} catch (err) {
    MessageLog.trace("[ftrack] TB_sceneOpened hook failed: " + err);
}
