/*
 ftrack framework Javascript constants

 Copyright (c) 2014-2023 ftrack
*/

// Event topics

const BASE_TOPIC = "ftrack.framework"

const TOPIC_INTEGRATION_ALIVE = BASE_TOPIC + ".integration-alive";
// Sent from integration to standalone process to initiate connection.
// Sent from standalone process to integration to indicate to check if integration is alive

const TOPIC_ACK = BASE_TOPIC + ".ack";
// Sent back to standalone process to acknowledge receipt of event TOPIC_INTEGRATION_ALIVE

const TOPIC_CONTEXT_DATA = BASE_TOPIC + ".context-data";
// Return event from standalone process on TOPIC_INTEGRATION_ALIVE event sent from integration,
// contains context data.
