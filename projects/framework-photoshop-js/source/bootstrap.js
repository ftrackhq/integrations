/*
 ftrack Photoshop framework bootstrap

 Copyright (c) 2014-2023 ftrack
*/

var csInterface = new CSInterface();

var event_manager = undefined;
var remote_integration_session_id = undefined;
var connected = false;
var panel_launchers;

try {
    function jsx_callback(){
        console.log("ps.jsx loaded");
    }

    jsx.evalFile('./ps.jsx', jsx_callback);
} catch (e) {
    error("[INTERNAL ERROR] Failed to load JSX resource "+e+" Details: "+e.stack);
}

function initializeIntegration() {
    /* Initialise the Photoshop JS integration part. */
    try {
        var env = {};

        // Get app version

        var hostEnv = csInterface.getHostEnvironment();
        var appVersion = parseInt(hostEnv.appVersion.split('.')[0]);

        // TODO: when CEP is deprecated, prevent initialization and show error message

        // Fetch launch variables passed on by Connect (hook)
        csInterface.evalScript('$.getenv("FTRACK_REMOTE_INTEGRATION_SESSION_ID")', function (result) {
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
        remote_integration_session_id = env.FTRACK_REMOTE_INTEGRATION_SESSION_ID;

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

        // Settle down - wait for standalone process compile to start listening. Then send
        // a ping to the standalone process to connect.
        sleep(1500).then(() => {
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
        error("[INTERNAL ERROR] Failed to publish standalone process discovery event! "+e+" Details: "+e.stack);
    }
}

// Event

function prepareEventData(data) {
    /* Append integration session id to event data */
    data["remote_integration_session_id"] = remote_integration_session_id;
    return data;
}

function handleIntegrationContextDataCallback(event) {
    /* Standalone process has sent context data */
    try {
        if (event.data.remote_integration_session_id != remote_integration_session_id)
            return;
        if (!connected) {
            connected = true;
            showElement("connecting", false);
            showElement("content", true);
            alert("ftrack Photoshop Integration successfully initialized\n\nIMPORTANT NOTE: "+
            "This is an beta and not intended for production use. Please submit bug reports "+
            "and feedback to support@ftrack.com.");
        }
        // Build launchers
        panel_launchers = event.data.panel_launchers;

        let launcher_table = document.getElementById("launchers");
        let idx = 0;
        while (idx < panel_launchers.length) {
            let launcher = panel_launchers[idx];
            let row = launcher_table.insertRow();
            let cell = row.insertCell();
            cell.innerHTML = '<button id="launcher_button" onclick="launchTool(\''+launcher.name+'\')"><img id="launcher_image" src="./image/'+launcher.image+'.png" border="0" />&nbsp;'+launcher.label+'</button>';
            idx++;
        }
    } catch (e) {
        error("[INTERNAL ERROR] Failed setting up panel! "+e+" Details: "+e.stack);
    }

    // TODO: Display received context info
}

function handleIntegrationDiscoverCallback(event) {
    /* Tell integration we are still here by sending reply back */
    if (event.data.remote_integration_session_id !== remote_integration_session_id)
        return;
    event_manager.publish_reply(event, prepareEventData({}));
}

initializeIntegration();
