/*
 ftrack Photoshop framework bootstrap

 Included

 Copyright (c) 2024 ftrack
*/

try {
    function jsx_callback(){
        console.log("ps-include.jsx loaded");
    }

    jsx.evalFile('./ps-include.jsx', jsx_callback);
} catch (e) {
    error("[INTERNAL ERROR] Failed to load JSX resource "+e+" Details: "+e.stack);
}

// Add additional logic here

//  Example on how to a an additional PS API function to be callable from Python host
// RPC_FUNCTION_MAPPING["helloWorld"] = "helloWorld";
