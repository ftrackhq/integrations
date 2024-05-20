/**
 * Harmony ftrack integration
 * 
 * User extensions, exists as a template and is intended to be overridden by the user.
 */
"use strict";

const EXTENSION_TYPE="js_functions"
const EXTENSION_NAME="framework-harmony-user"

function processUserEvent(integration, topic, data, id) {
	info("(User extension) Processing incoming '"+topic+"' event: "+JSON.stringify(data));
}

info("(Template user extensions) Loaded");