/*
 ftrack Adobe Premiere framework integration bootstrap

 Copyright (c) 2024 ftrack
*/


function jsx_callback(){
    console.log("pp.jsx loaded");
}

try {
    jsx.evalFile('./pp.jsx', jsx_callback);
} catch (e) {
    error("[INTERNAL ERROR] Failed to load JSX resource "+e+" Details: "+e.stack);
}

function jsx_include_callback(){
    console.log("pp-include loaded");
}

// Load custom extension JSX if exists
try {
    jsx.evalFile('./pp-include.jsx', jsx_include_callback);
} catch (e) {
    console.log("[WARNING] Failed to load JSX include resource "+e+" Details: "+e.stack);
}

// Whitelisted functions and their mappings, add entrypoints from ps.jsx here
window.FTRACK_RPC_FUNCTION_MAPPING = {
    render:"render",
};

window.ftrackInitialiseExtension = function(session, event_manager, remote_integration_session_id) {
    // Do additional initialisations here
};


window.ftrackIntegrationConnected = function() {
    // React upon integration connected
};


