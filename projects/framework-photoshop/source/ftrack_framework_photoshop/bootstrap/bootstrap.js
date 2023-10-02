/*
 ftrack Photoshop framework bootstrap

 Copyright (c) 2014-2023 ftrack
*/

var event_manager = undefined;
var adobe_id = undefined;
var connected = false;

function initializeIntegration() {

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
        error("[INTERNAL ERROR] Failed to initialise integration! "+e);
    }
}


function initializeSession(env, appVersion) {
    try {
        adobe_id = env.FTRACK_INTEGRATION_SESSION_ID;

        var session = new ftrack.Session(
            env.FTRACK_SERVER,
            env.FTRACK_API_USER,
            env.FTRACK_API_KEY,
            { autoConnectEventHub: true }
        );

        event_manager = new EventManager(session, adobe_id);

        // Subscribe to events
        event_manager.subscribe(
            TOPIC_CONTEXT_DATA,
            handleContextData
        );
        event_manager.subscribe(
            TOPIC_INTEGRATION_ALIVE,
            handleIntegrationAlive
        );

        // Settle down - wait for standalone process to start listening. Then send
        // a ping to the standalone process to connect.
        sleep(500).then(() => {
            try {
                event_manager.publish(TOPIC_INTEGRATION_ALIVE, {"version": appVersion});
            } catch (e) {
                error("[INTERNAL ERROR] Failed to publish integration alive event! "+e);
            }
        });

    } catch (e) {
        error("[INTERNAL ERROR] Failed to initialise ftrack session! "+e);
    }
}

function handleContextData(event) {

    if (!connected) {
        connected = true;
        showElement("connecting", false);
        showElement("content", true);
        alert("ftrack Photoshop Integration successfully initialized\n\nIMPORTANT NOTE: "+
        "This is an alpha and not intended for production use. Please submit bug reports "+
        "and feedback to support@ftrack.com.");
    }
    // TODO: Display context info
}

function handleIntegrationAlive(event) {
    // Tell integration we are still here by sending reply back
    sendEvent(TOPIC_ACK, {}, event.id);
}


initializeIntegration();
