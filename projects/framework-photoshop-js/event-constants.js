/*
 ftrack framework Javascript constants

 Copyright (c) 2014-2023 ftrack
*/

// Event

const _BASE_ = "ftrack.framework"

const REMOTE_ALIVE_TOPIC = _BASE_ + ".remote.alive";
// Sent from integration to standalone process to initiate connection.
// Sent from standalone process to integration on connect (uxp) and to check if
// integration is alive.

const REMOTE_ALIVE_ACK_TOPIC = _BASE_ + ".remote.alive.ack";
// Sent back to standalone process to acknowledge receipt of event REMOTE_ALIVE_TOPIC

const REMOTE_CONTEXT_DATA_TOPIC = _BASE_ + ".remote.context.data";
// Return event from standalone process on REMOTE_ALIVE_TOPIC event sent from integration,
// contains context data.
