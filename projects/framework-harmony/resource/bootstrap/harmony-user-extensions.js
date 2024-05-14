/**
 * Harmony ftrack integration
 * 
 * Base extensions
 */
"use strict";

const EXTENSION_TYPE="js_functions"
const EXTENSION_NAME="framework-harmony-user"



function processUserEvent(integration, topic, data, id) {
	info("(User extension) Processing incoming '"+topic+"' event: "+JSON.stringify(data));
}

