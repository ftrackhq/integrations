/*
 ftrack Adobe After Effects framework integration bootstrap

 Copyright (c) 2024 ftrack
*/


function jsx_callback(){
    console.log("af.jsx loaded");
}

try {
    jsx.evalFile('./af.jsx', jsx_callback);
} catch (e) {
    error("[INTERNAL ERROR] Failed to load JSX resource "+e+" Details: "+e.stack);
}

function jsx_include_callback(){
    console.log("af-include loaded");
}

// Load custom extension JSX if exists
try {
    jsx.evalFile('./af-include.jsx', jsx_include_callback);
} catch (e) {
    console.log("[WARNING] Failed to load JSX include resource "+e+" Details: "+e.stack);
}

// Whitelisted functions and their mappings, add entrypoints from ps.jsx here
window.FTRACK_RPC_FUNCTION_MAPPING = {
    getProjectPath:"getProjectPath",
    saveProject:"saveProject",
    saveProjectAs:"saveProjectAs",
    getOutputModuleTemplateNames:"getOutputModuleTemplateNames",
    render:"render",
    openProject:"openProject",
};

window.ftrackInitialiseExtension = function(session, event_manager, remote_integration_session_id) {
    // Do additional initialisations here
};


window.ftrackIntegrationConnected = function() {
    // React upon integration connected
};


