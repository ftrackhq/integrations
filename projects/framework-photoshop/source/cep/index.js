/*
 ftrack Photoshop framework integration

 Copyright (c) 2014-2023 ftrack
*/

var csInterface = new CSInterface();

const TOPIC_PING = "ftrack.framework.ping";
const TOPIC_PONG = "ftrack.framework.pong";


var env = {};
var session = undefined;
var adobe_id = undefined;
var connected = false;

function showElement(element_id, show) {
    document.getElementById(element_id).style.visibility = show?"visible":"hidden";
    document.getElementById(element_id).style.display = show?"block":"none";     
}

function error(message) {
    showElement("connecting", false);
    document.getElementById("error").innerHTML = message;
    showElement("error", true);
    alert(message);
}

// Init

function initializeSession(appVersion) {
    try {
        adobe_id = env.FTRACK_INTEGRATION_SESSION_ID;

        session = new ftrack.Session(
            env.FTRACK_SERVER,
            env.FTRACK_API_USER,
            env.FTRACK_API_KEY,
            { autoConnectEventHub: true }
        );

        // Subscribe to events
        session.eventHub.subscribe(
            "topic="+TOPIC_PING,
            handleEvent
        );
        session.eventHub.subscribe(
            "topic="+TOPIC_PONG,
            handleEvent
        );

        // Settle down - wait for standalone process to start listening. Then send
        // a ping to the standalone process to connect.
        sleep(500).then(() => {
            sendEvent(TOPIC_PING, {"version": appVersion});
        });

    } catch (e) {
        error("[INTERNAL ERROR] Failed to initialise ftrack session! "+e);
    }
}


function initializeIntegration() {
    // Get app version

    var hostEnv = csInterface.getHostEnvironment();
    var appVersion = parseInt(hostEnv.appVersion.split('.')[0]);

    // TODO: when CEP is deprecated, prevent initialization and show error message

    env = {};
    try {
        // Fetch launch variables passed on by Connect (hook)
        csInterface.evalScript('$.getenv("FTRACK_INTEGRATION_SESSION_ID")', function (result) {
            if (result != 'null') {
                env.FTRACK_INTEGRATION_SESSION_ID = result;
                csInterface.evalScript('$.getenv("FTRACK_SERVER")', function (result) {
                    if (result != 'null') {
                        env.FTRACK_SERVER = result;
                        csInterface.evalScript('$.getenv("FTRACK_API_USER")', function (result) {
                            if (result != 'null') {
                                env.FTRACK_API_USER = result;
                                csInterface.evalScript('$.getenv("FTRACK_API_KEY")', function (result) {
                                    if (result != 'null') {
                                        env.FTRACK_API_KEY = result;
                                        initializeSession(appVersion);
                                    }
                                });
                            }
                        });
                    }
                });
            } else {
                error("No ftrack environment variable(s) available, make sure you launch Photoshop from ftrack (task)!");
            }
        });
    } catch (e) {
        error("[INTERNAL ERROR] Failed to read environment variables! "+e);
    }
}


// Events

function createEvent(topic, framework_data) {
    framework_data.integration_session_id = adobe_id;
    let event = new ftrack.Event(topic, framework_data);
    return event;
}

function sendEvent(topic, framework_data, reply_to_event) {
    if (reply_to_event !== undefined) {
        framework_data.reply_to_event = reply_to_event;
    }
    let event = createEvent(topic, framework_data);
    console.log("Publishing event: "+JSON.stringify(event));
    session.eventHub.publish(event);
}

function handleEvent(event) {

    if (event.source == undefined || event.data == undefined || event.source.applicationId === 'ftrack.api.javascript' ||
        event.data.integration_session_id == undefined || event.data.integration_session_id != adobe_id) {
        return;
    }

    console.log('(HUB) Received event from standalone process: ' + JSON.stringify(event));
    if (event.topic == TOPIC_PONG) {
        if (!connected) {
            connected = true;
            showElement("connecting", false); 
            showElement("content", true); 
            alert("ftrack Photoshop Integration successfully initialized\n\nIMPORTANT NOTE: This is a prototype and not intended for production use. Please submit bug reports and feedback to support@ftrack.com.");
        }
        // TODO: Display context info
    } else if (event.topic == TOPIC_PING) {
        // Tell integration we are still here
        sendEvent(TOPIC_PONG, {}, event.id);
    }
}

// Tools

// TODO: Implement tool launchers

// Utility

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

try {
    initializeIntegration();
} catch (e) {
    error("[INTERNAL ERROR] Failed to initialise integration! "+e);
}