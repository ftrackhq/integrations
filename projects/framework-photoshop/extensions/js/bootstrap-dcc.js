/*
 ftrack Adobe Photoshop framework integration bootstrap

 Copyright (c) 2024 ftrack
*/


function jsx_callback(){
    console.log("ps.jsx loaded");
}

try {
    jsx.evalFile('./ps.jsx', jsx_callback);
} catch (e) {
    error("[INTERNAL ERROR] Failed to load JSX resource "+e+" Details: "+e.stack);
}

function jsx_include_callback(){
    console.log("ps-include loaded");
}

// Load custom extension JSX if exists
try {
    jsx.evalFile('./ps-include.jsx', jsx_include_callback);
} catch (e) {
    console.log("[WARNING] Failed to load JSX include resource "+e+" Details: "+e.stack);
}

// Whitelisted functions and their mappings, add entrypoints from ps.jsx here
window.FTRACK_RPC_FUNCTION_MAPPING = {
    hasDocument:"hasDocument",
    documentSaved:"documentSaved",
    getDocumentPath:"getDocumentPath",
    getDocumentData:"getDocumentData",
    saveDocument:"saveDocument",
    exportDocument:"exportDocument",
    openDocument:"openDocument",
};

window.initialiseExtension = function(session) {
    // Do additional initialisations here
};

