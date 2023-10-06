
global.fetch = require('node-fetch');
const ftrack = require("@ftrack/api");

console.log(ftrack);

error = console.error;

class CSInterface {

    getHostEnvironment() {
        return {
            appVersion: "1.0"
        }
    }

    evalScript(
        scriptString,
        callback
    ) {
        console.log('Resolving', scriptString);
        if (scriptString.startsWith('$.getenv("')) {
            var envVariableName = scriptString.replace('$.getenv("', '').replace('")', '');
            callback(process.env[envVariableName] || "null");
            return
        }

        throw Error("Unknown scriptString to eval: " + scriptString);
    }

}

// console.log(process.env)
/*
 ftrack framework Javascript utils

 Copyright (c) 2014-2023 ftrack
*/

function sleep(ms) {
    /* Sleep for *ms* milliseconds and then continue execution. */
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showElement(element_id, show) {
    /* Show or hide element with *element_id*, based on boolean *show* */
    document.getElementById(element_id).style.visibility = show?"visible":"hidden";
    document.getElementById(element_id).style.display = show?"block":"none";
}

function error(message) {
    /* Show error *message*, hiding connecting element. */
    showElement("connecting", false);
    document.getElementById("error").innerHTML = message;
    showElement("error", true);
    alert(message);
}/*
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
/*
 ftrack framework Javascript core

 Copyright (c) 2014-2023 ftrack
*/

// Events

class EventManager {
    /*
    * ftrack Framework JS event manager
    */

    constructor(session) {
        this._session = session;

        this.publish = new Publish(this);
        this.subscribe = new Subscribe(this);
    }

    get session() {
        // Return the session
        return this._session;
    }

    _subscribe(topic, callback_fn) {
        this.session.eventHub.subscribe("topic="+topic, this.handle_event.bind(
            this, callback_fn
        ));
    }

    handle_event(callback_fn, event) {
        // Handle and validate an incoming event - ignore Javascript events
        if (event.source == undefined || event.data == undefined ||
            event.source.applicationId === 'ftrack.api.javascript') {
            return;
        }
        console.log("Received event: " + JSON.stringify(event));
        callback_fn(event);
    }

    _publish(topic, data) {
        let event = new ftrack.Event(topic, data);
        this.session.eventHub.publish(event);
    }

    publish_reply(surce_event, data) {
        this.session.eventHub.publishReply(surce_event, data);
    }
};


class Publish {
    /*
    * Class with all the events published by the JS framework
    */

    constructor(event_manager) {
        this._event_manager = event_manager;
    }

    get event_manager() {
        // Return the session
        return this._event_manager;
    }

    discover_remote_integration(data) {
        let event_topic = DISCOVER_REMOTE_INTEGRATION_TOPIC;
        this.event_manager._publish(event_topic, data);
    }

};

class Subscribe {
    /*
    * Class with all the events subscribed by the JS framework
    */

    constructor(event_manager) {
        this._event_manager = event_manager;
    }

    get event_manager() {
        // Return the session
        return this._event_manager;
    }

    discover_remote_integration(callback) {
        let event_topic = DISCOVER_REMOTE_INTEGRATION_TOPIC;
        this.event_manager._subscribe(event_topic, callback);
    }

    integration_context_data(callback) {
        let event_topic = REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC;
        this.event_manager._subscribe(event_topic, callback);
    }

};


/*
 ftrack Photoshop framework bootstrap

 Copyright (c) 2014-2023 ftrack
*/

var event_manager = undefined;
var integration_session_id = undefined;
var connected = false;

function initializeIntegration() {
    /* Initialise the Photoshop JS integration part. */
    try {
        var csInterface = new CSInterface();
        var env = {};

        // Get app version

        var hostEnv = csInterface.getHostEnvironment();
        var appVersion = parseInt(hostEnv.appVersion.split('.')[0]);

        // TODO: when CEP is deprecated, prevent initialization and show error message

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
                                        initializeSession(env, appVersion);
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
        error("[INTERNAL ERROR] Failed to initialise integration! "+e+" Details: "+e.stack);
    }
}


function initializeSession(env, appVersion) {
    /* Initialise the ftrack API session. */
    try {
        integration_session_id = env.FTRACK_INTEGRATION_SESSION_ID;

        var session = new ftrack.Session(
            env.FTRACK_SERVER,
            env.FTRACK_API_USER,
            env.FTRACK_API_KEY,
            { autoConnectEventHub: true }
        );

        event_manager = new EventManager(session);

        //  Subscribe to events
        event_manager.subscribe.discover_remote_integration(
            handleIntegrationDiscoverCallback
        );
        event_manager.subscribe.integration_context_data(
            handleIntegrationContextDataCallback

        );

        // Settle down - wait for standalone process to start listening. Then send
        // a ping to the standalone process to connect.
        sleep(500).then(() => {
            connect(appVersion);
        });

    } catch (e) {
        error("[INTERNAL ERROR] Failed to initialise ftrack session! "+e+" Details: "+e.stack);
    }
}

function connect(appVersion) {
    /* Initiate connection with standalone Python part. */
    try {
        console.log('Publishing event!');
        event_manager.publish.discover_remote_integration(
            prepareEventData({
                "version": appVersion,
            })
        );
    } catch (e) {
        error("[INTERNAL ERROR] Failed to publish integration discovery event! "+e+" Details: "+e.stack);
    }
}

// Event

function prepareEventData(data) {
    /* Append integration session id to event data */
    data["integration_session_id"] = integration_session_id;
    return data;
}

function handleIntegrationContextDataCallback(event) {
    /* Standalone process has sent context data */
    if (event.data.integration_session_id != integration_session_id)
        return;
    if (!connected) {
        connected = true;
        showElement("connecting", false);
        showElement("content", true);
        alert("ftrack Photoshop Integration successfully initialized\n\nIMPORTANT NOTE: "+
        "This is an alpha and not intended for production use. Please submit bug reports "+
        "and feedback to support@ftrack.com.");
    }
    // TODO: Display received context info
}

function handleIntegrationDiscoverCallback(event) {
    /* Tell integration we are still here by sending reply back */
    if (event.data.integration_session_id !== integration_session_id)
        return;
    event_manager.publish_reply(event, prepareEventData({}));
}


initializeIntegration();
