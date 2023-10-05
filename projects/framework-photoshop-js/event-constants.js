/*
 ftrack framework Javascript constants

 Copyright (c) 2014-2023 ftrack
*/

// Event

const _BASE_ = "ftrack.framework"

const DISCOVER_REMOTE_INTEGRATION_TOPIC = _BASE_ + ".discover.remote.integration";
// Sent from integration to standalone process to initiate connection.
// Sent from standalone process to integration on connect (uxp) and to check if
// integration is alive.

const REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC = _BASE_ + ".remote.integration.context.data";
// Sent back from standalone process to integration supplying context data.
