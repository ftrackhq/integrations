/*
 ftrack Photoshop framework bootstrap

 Copyright (c) 2014-2023 ftrack
*/

var event_manager = undefined;
var integration_session_id = undefined;
var connected = false;

try {
    function jsx_callback(){
        alert("ps.jsx loaded");
    }

    jsx.evalFile('./ps.jsx', jsx_callback);
} catch (e) {
    error("[INTERNAL ERROR] Failed to resource "+e+" Details: "+e.stack);
}

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
        event_manager.subscribe.remote_integration_rpc(
            handleRemoteIntegrationRPCCallback
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

function replyRPCCallback(event, result) {
    /* Reply to RPC call from standalone process event with result */
    event_manager.publish_reply(event, prepareEventData(
    {
        "result": result
    }
    ));
}

function handleRemoteIntegrationRPCCallback(event) {
    /* Handle RPC calls from standalone process - run function with arguments
     supplied in event and return the result.*/
    try {
        if (event.data.integration_session_id !== integration_session_id)
            return;
        let function_name = event.data.function;
        let args = event.data.args;
        let kwargs = event.data.kwargs;

        window[function_name](
            replyRPCCallback.bind(event),
            ...args,
            ...kwargs
        );
    } catch (e) {
        error("[INTERNAL ERROR] Failed to run RPC call! "+e+" Details: "+e.stack);
    }
 }

// Tool launch

function launchPublisher() {
    event_manager.publish.remote_integration_run_dialog(
        prepareEventData({
            "dialog_name": "framework_publisher_dialog",
        })
    );
}

// Photoshop CEP interface functions

function getDocumentData(callback) {
    /* Get document data from Photoshop and return to callback.*/
    var result = undefined;
    csInterface.evalScript('getDocumentData()', function (result) {
        callback(JSON.parse(result));
    });
}

initializeIntegration();
