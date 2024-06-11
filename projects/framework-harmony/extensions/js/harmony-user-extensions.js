/**
 * Harmony ftrack integration
 *
 * User extension
 * 
 * Copyright (c) 2024 ftrack
 */
"use strict";

const EXTENSION_TYPE="functions_js"
const EXTENSION_NAME="framework-harmony-user"

/**
* Perform additional optional extension bootstrap
*
* @param {Integration} integration
*/
function ftrackInitialiseExtension(integration) {
    info("(User extension) Initialising extension");
}

/**
* Optionally act upon integration connected
*
* @param {Integration} integration
*/
function ftrackIntegrationConnected(integration) {
    info("(User extension) Integration connected");
}

/**
* Optionally act an incoming event
*
* @param {Integration} integration
* @param {string} event topic
* @param {object} event data
* @param {string} event id
*/
function processUserEvent(integration, topic, data, id) {
	info("(User extension) Processing incoming '"+topic+"' event: "+JSON.stringify(data));
	return false;
}

// Add RPC functions here


info("(User extension) Loaded");


