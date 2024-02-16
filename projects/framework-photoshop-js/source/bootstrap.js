/*
 ftrack Photoshop framework bootstrap

 Copyright (c) 2014-2023 ftrack
*/

var csInterface = new CSInterface();

var event_manager = undefined;
var remote_integration_session_id = undefined;
var connected = false;
var panel_launchers;
var context_id = undefined;
var project_id = undefined;

function jsx_callback(){
    console.log("ps.jsx loaded");
}

try {
    jsx.evalFile('./ps.jsx', jsx_callback);
} catch (e) {
    error("[INTERNAL ERROR] Failed to load JSX resource "+e+" Details: "+e.stack);
}

// Load custom extension JSX if exists
try {
    jsx.evalFile('./ps-include.jsx', jsx_callback);
} catch (e) {
    console.log("[WARNING] Failed to load JSX include resource "+e+" Details: "+e.stack);
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
                env.FTRACK_REMOTE_INTEGRATION_SESSION_ID = result;
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
        // Build launchers
        if (event.data.panel_launchers !== undefined) {
            panel_launchers = event.data.panel_launchers;

            let launcher_table = document.getElementById("launchers");
            launcher_table.innerHTML = "";
            let idx = 0;
            while (idx < panel_launchers.length) {
                let launcher = panel_launchers[idx];
                let row = launcher_table.insertRow();
                let cell = row.insertCell();
                cell.innerHTML = '<button id="launcher_button" onclick="launchTool(\''+launcher.name+'\')"><img id="launcher_image" src="./image/'+launcher.icon+'.png" border="0" />&nbsp;'+launcher.label+'</button>';
                idx++;
            }
        }
        if (event.data.context_id !== context_id) {
            context_id = event.data.context_id;
            project_id = event.data.project_id;
            document.getElementById("context_thumbnail").src = event.data.context_thumbnail;
            document.getElementById("context_name").innerHTML = event.data.context_name;
            document.getElementById("context_path").innerHTML = event.data.context_path;
        }
        if (!connected) {
            connected = true;
            showElement("connecting", false);
            showElement("content", true);
        } else {
            // Reply to event to confirm we received the data
            event_manager.publish_reply(event, prepareEventData(
                {
                    "result": true
                }
            ));
        }
    } catch (e) {
        error("[INTERNAL ERROR] Failed setting up panel! "+e+" Details: "+e.stack);
    }

    // TODO: Display received context info
}

// Tool launch

function launchTool(tool_name) {
    // Find dialog name
    let idx = 0;
    var dialog_name = undefined, tool_configs = undefined;
    while (idx < panel_launchers.length) {
        let launcher = panel_launchers[idx];
        if (launcher.name == tool_name) {
            dialog_name = launcher.dialog_name;
            tool_configs = launcher.options.tool_configs;
            break;
        }
        idx++;
    }
    event_manager.publish.remote_integration_run_dialog(
        prepareEventData({
            "dialog_name": dialog_name,
            "tool_configs": tool_configs
        })
    );
}

// RPC - extendscript API calls

// Whitelisted functions and their mappings, add entrypoints from ps.jsx here
var RPC_FUNCTION_MAPPING = {
    hasDocument:"hasDocument",
    documentSaved:"documentSaved",
    getDocumentPath:"getDocumentPath",
    getDocumentData:"getDocumentData",
    saveDocument:"saveDocument",
    exportDocument:"exportDocument",
    openDocument:"openDocument",
};

function handleRemoteIntegrationRPCCallback(event) {
    /* Handle RPC calls from standalone process - run function with arguments
     supplied in event and return the result.*/
    try {
        if (event.data.remote_integration_session_id !== remote_integration_session_id)
            return;
        let function_name_raw = event.data.function_name;
        let function_name = RPC_FUNCTION_MAPPING[function_name_raw];

        if (function_name === undefined || function_name.length === 0) {
            event_manager.publish_reply(event, prepareEventData(
                {
                    "error_message": "Unknown RCP function '"+function_name+"'"
                }
            ));
            return;
        }
        // Build args, quote strings
        let s_args = '';
        let idx = 0;
        while (idx < event.data.args.length) {
            let value = event.data.args[idx];
            if (typeof value === 'string')
                value = '"' + value + '"';
            s_args += (s_args.length>0?",":"") + value;
            idx++;
        }

        csInterface.evalScript(function_name+'('+s_args+')', function (result) {
            try {
                // String is the evalScript type, decode
                if (result.startsWith("{"))
                    result = JSON.parse(result);
                else if (result === "true")
                    result = true;
                else if (result === "false")
                    result = false;
                event_manager.publish_reply(event, prepareEventData(
                    {
                        "result": result
                    }
                ));
            } catch (e) {
                error_message = "[INTERNAL ERROR] Failed to convert RPC call result '"+result+"'! "+e+" Details: "+e.stack;
                event_manager.publish_reply(event, prepareEventData(
                    {
                        "error_message": error_message
                    }
                ));
                error(error_message);
            }
        });
    } catch (e) {
        error_message = "[INTERNAL ERROR] Failed to run RPC call! "+e+" Details: "+e.stack;
        event_manager.publish_reply(event, prepareEventData(
            {
                "error_message": error_message
            }
        ));
        error(error_message);
    }
 }


function openContext() {
    let task_url = event_manager.session.serverUrl+"/#slideEntityId="+context_id+"&slideEntityType=task&view=tasks&itemId=projects&entityId="+project_id+"&entityType=show";
    csInterface.openURLInDefaultBrowser(task_url);
}

initializeIntegration();
