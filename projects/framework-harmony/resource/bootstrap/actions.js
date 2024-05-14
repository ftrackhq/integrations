/**
 * Harmony ftrack integration
 * 
 * Actions, called from menu
 */
"use strict";

function launchTool(tool_name) {
    getIntegration().launchTool(tool_name);
    /*var app = QCoreApplication.instance();
    if (app.integration != undefined) {
        app.integration.launchTool(tool_name);
    } else {
        MessageLog.trace("[ftrack] Can't open tool - integration not initialised yet!");
    }*/
}
