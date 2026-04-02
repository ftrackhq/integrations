/*
 ftrack Adobe framework integration common bootstrap (UXP)

 Copyright (c) 2026 ftrack
*/

const os = require("os");
const { shell } = require("uxp");
const { storage } = require("uxp");
const { app } = require("photoshop");


var event_manager = undefined;
var remote_integration_session_id = undefined;
var connected = false;
var panel_launchers;
var context_id = undefined;
var project_id = undefined;
var panel_bindings_initialized = false;

const CONNECT_DELAY_MS = 7000;
const UI_ISOLATION_MODE = true;
const LOCAL_CONTEXT_THUMBNAIL_PATH = "./icons/thumbnail.png";


function platformPathJoin(parts) {
    const separator = os.platform().indexOf("win") === 0 ? "\\" : "/";
    return parts.join(separator);
}


function getDefaultBootstrapPath() {
    return platformPathJoin([
        os.homedir(),
        ".ftrack",
        "framework-photoshop",
        "uxp-bootstrap",
        "bootstrap-latest.json",
    ]);
}


function isValidBootstrapData(data) {
    if (!data || typeof data !== "object") {
        return false;
    }

    const requiredKeys = [
        "server_url",
        "api_user",
        "api_key",
        "remote_integration_session_id",
    ];

    for (let index = 0; index < requiredKeys.length; index += 1) {
        const key = requiredKeys[index];
        if (!data[key]) {
            return false;
        }
    }

    return true;
}


function toFileUrl(path) {
    if (typeof path !== "string") {
        throw new Error("Invalid path type");
    }

    const normalized = path.replace(/\\/g, "/");
    if (normalized.indexOf("file:") === 0) {
        return normalized;
    }

    if (normalized.indexOf("/") === 0) {
        return "file:" + normalized;
    }

    return "file:/" + normalized;
}


async function readJsonFile(path) {
    const fs = storage.localFileSystem;
    const entry = await fs.getEntryWithUrl(toFileUrl(path));
    const raw = await entry.read();
    return JSON.parse(raw);
}


async function loadBootstrapData() {
    const candidatePaths = [];
    const defaultPath = getDefaultBootstrapPath();

    candidatePaths.push(defaultPath);

    const cachedPath = localStorage.getItem("ftrack.photoshop.bootstrap_path");
    if (cachedPath && cachedPath !== defaultPath) {
        candidatePaths.push(cachedPath);
    }

    for (let index = 0; index < candidatePaths.length; index += 1) {
        const path = candidatePaths[index];
        try {
            const data = await readJsonFile(path);
            if (!isValidBootstrapData(data)) {
                continue;
            }
            localStorage.setItem("ftrack.photoshop.bootstrap_path", path);
            return data;
        } catch (error) {
            console.log(
                "[INFO] Could not read bootstrap file " + path + ": " + error,
            );
        }
    }

    return null;
}


function getAppVersionMajor() {
    const rawVersion = String(app.version || "0");
    const parsed = parseInt(rawVersion.split(".")[0], 10);
    if (Number.isNaN(parsed)) {
        return 0;
    }
    return parsed;
}


function logPanel(message) {
    console.log("[ftrack panel] " + message);
}


function installGlobalErrorHandlers() {
    if (window.__ftrack_global_error_handlers_installed__) {
        return;
    }

    window.__ftrack_global_error_handlers_installed__ = true;

    window.addEventListener("error", (event) => {
        try {
            const error = event && event.error;
            const message = event && event.message ? event.message : "<no message>";
            const stack = error && error.stack ? error.stack : "<no stack>";
            console.error("[ftrack panel] Global error: " + message + " stack: " + stack);
        } catch (handlerError) {
            console.error("[ftrack panel] Failed in global error handler.", handlerError);
        }
    });

    window.addEventListener("unhandledrejection", (event) => {
        try {
            const reason = event && event.reason ? event.reason : "<no reason>";
            console.error("[ftrack panel] Unhandled promise rejection:", reason);
        } catch (handlerError) {
            console.error("[ftrack panel] Failed in rejection handler.", handlerError);
        }
    });

    logPanel("Global error handlers installed.");
}


function ensurePanelBindings() {
    if (panel_bindings_initialized) {
        return;
    }

    const contextOpenButton = document.getElementById("context_open");
    if (!contextOpenButton) {
        console.warn("[ftrack panel] Missing context_open button while binding events.");
        return;
    }

    contextOpenButton.addEventListener("click", () => {
        openContext();
    });

    panel_bindings_initialized = true;
    logPanel("Static panel events bound.");
}


function clearElementChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}


function renderPanelLaunchers(launchers) {
    const launcherTable = document.getElementById("launch_configs");
    if (!launcherTable) {
        throw new Error("Missing launch_configs element.");
    }

    clearElementChildren(launcherTable);

    if (UI_ISOLATION_MODE) {
        logPanel("UI isolation mode enabled: skipping launcher rendering.");
        return;
    }

    if (!Array.isArray(launchers)) {
        console.warn("[ftrack panel] panel_launchers payload is not an array.");
        return;
    }

    for (let idx = 0; idx < launchers.length; idx += 1) {
        const launcher = launchers[idx];
        if (!launcher || !launcher.name) {
            continue;
        }

        const row = document.createElement("tr");
        const cell = document.createElement("td");

        const button = document.createElement("button");
        button.type = "button";
        button.className = "launcher_button";
        button.addEventListener("click", () => {
            launchTool(launcher.name);
        });

        const image = document.createElement("img");
        image.className = "launcher_image";
        image.src = "./icons/" + launcher.icon + ".png";
        image.alt = launcher.label || launcher.name;

        const label = document.createElement("span");
        label.textContent = launcher.label || launcher.name;

        button.appendChild(image);
        button.appendChild(label);
        cell.appendChild(button);
        row.appendChild(cell);
        launcherTable.appendChild(row);
    }
}


function updatePanelContext(data) {
    const contextThumbnail = document.getElementById("context_thumbnail");
    const contextName = document.getElementById("context_name");
    const contextPath = document.getElementById("context_path");

    if (!contextThumbnail || !contextName || !contextPath) {
        throw new Error("Missing context panel elements.");
    }

    if (UI_ISOLATION_MODE) {
        contextThumbnail.src = LOCAL_CONTEXT_THUMBNAIL_PATH;
        if (data.context_thumbnail) {
            logPanel("UI isolation mode enabled: skipping remote thumbnail assignment.");
        }
    } else {
        contextThumbnail.src = data.context_thumbnail || LOCAL_CONTEXT_THUMBNAIL_PATH;
    }

    contextName.textContent = data.context_name || "";
    contextPath.textContent = data.context_path || "";
}


async function initializeIntegration() {
    /* Initialise the JS integration. */
    try {
        installGlobalErrorHandlers();
        ensurePanelBindings();
        logPanel("Initialising integration.");

        const env = await loadBootstrapData();
        if (!env) {
            error(
                "No ftrack bootstrap data available, make sure you launch Photoshop from a task within ftrack Studio or Connect!",
                false,
            );
            return;
        }

        logPanel("Bootstrap data loaded.");
        initializeSession(env, getAppVersionMajor());
    } catch (e) {
        console.error("[INTERNAL ERROR] Failed to initialise integration!", e);
        error("[INTERNAL ERROR] Failed to initialise integration! " + e + " Details: " + e.stack, false);
    }
}


function initializeSession(env, appVersion) {
    /* Initialise the ftrack API session. */
    try {
        logPanel("Initialising session.");
        remote_integration_session_id = env.remote_integration_session_id;

        var session = new ftrack.Session(
            env.server_url,
            env.api_user,
            env.api_key,
            { autoConnectEventHub: true },
        );

        event_manager = new EventManager(session);

        event_manager.subscribe.integration_context_data(
            handleIntegrationContextDataCallback,
        );
        event_manager.subscribe.remote_integration_rpc(
            handleRemoteIntegrationRPCCallback,
        );

        logPanel("Event subscriptions ready.");

        sleep(CONNECT_DELAY_MS).then(() => {
            logPanel(
                "Publishing discover event after startup delay of " +
                String(CONNECT_DELAY_MS) +
                "ms.",
            );
            connect(appVersion);
        });

        try {
            ftrackInitialiseExtension(session, event_manager, remote_integration_session_id);
        } catch (e) {
            console.log(
                "[WARNING] Failed to initialise ftrack additional extensions! " +
                e +
                " Details: " +
                e.stack,
            );
        }
    } catch (e) {
        console.error("[INTERNAL ERROR] Failed to initialise ftrack session!", e);
        error("[INTERNAL ERROR] Failed to initialise ftrack session! " + e + " Details: " + e.stack, false);
    }
}


function connect(appVersion) {
    /* Initiate connection with standalone Python part. */
    try {
        event_manager.publish.discover_remote_integration(
            prepareEventData({
                version: appVersion,
            }),
        );
        logPanel("Discover event published.");
    } catch (e) {
        console.error("[INTERNAL ERROR] Failed to publish standalone process discovery event!", e);
        error("[INTERNAL ERROR] Failed to publish standalone process discovery event! " + e + " Details: " + e.stack, false);
    }
}


function prepareEventData(data) {
    /* Append integration session id to event data */
    data.remote_integration_session_id = remote_integration_session_id;
    return data;
}


function handleIntegrationContextDataCallback(event) {
    /* Standalone process has sent context data */
    try {
        logPanel("Handling integration context data event.");

        if (!event || !event.data) {
            console.warn("[ftrack panel] Ignoring malformed context data event.");
            return;
        }

        if (event.data.remote_integration_session_id !== remote_integration_session_id) {
            logPanel("Ignoring context event for different integration session.");
            return;
        }

        if (event.data.panel_launchers !== undefined) {
            logPanel("Rendering panel launchers.");
            panel_launchers = event.data.panel_launchers;

            try {
                renderPanelLaunchers(panel_launchers);
            } catch (launcherError) {
                console.error("[INTERNAL ERROR] Failed rendering launchers!", launcherError);
                throw launcherError;
            }

            logPanel("Panel launchers rendered.");
        }

        if (event.data.context_id !== context_id) {
            logPanel("Updating context details.");
            context_id = event.data.context_id;
            project_id = event.data.project_id;

            try {
                updatePanelContext(event.data);
            } catch (contextError) {
                console.error("[INTERNAL ERROR] Failed updating context fields!", contextError);
                throw contextError;
            }

            logPanel("Context details updated.");
        }

        if (!connected) {
            logPanel("Marking integration as connected.");
            connected = true;
            showElement("connecting", false);
            showElement("content", true);

            try {
                ftrackIntegrationConnected();
            } catch (e) {
                console.log("[WARNING] Failed to tell extension we are connected! " + e + " Details: " + e.stack);
            }
        } else {
            logPanel("Replying to context data event.");
            event_manager.publish_reply(
                event,
                prepareEventData({
                    result: true,
                }),
            );
        }
    } catch (e) {
        console.error("[INTERNAL ERROR] Failed setting up panel!", e);
        error("[INTERNAL ERROR] Failed setting up panel! " + e + " Details: " + e.stack, false);
    }
}


function launchTool(tool_name) {
    let idx = 0;
    var dialog_name = undefined;
    var tool_options = undefined;
    while (idx < panel_launchers.length) {
        let launcher = panel_launchers[idx];
        if (launcher.name === tool_name) {
            dialog_name = launcher.dialog_name;
            tool_options = launcher.options;
            break;
        }
        idx += 1;
    }
    event_manager.publish.remote_integration_run_dialog(
        prepareEventData({
            name: tool_name,
            dialog_name: dialog_name,
            options: tool_options,
        }),
    );
}


async function handleRemoteIntegrationRPCCallback(event) {
    if (!FTRACK_RPC_FUNCTION_MAPPING) {
        const error_message =
            "[INTERNAL ERROR] No RPC function mappings defined, please make sure to define FTRACK_RPC_FUNCTION_MAPPING in bootstrap-dcc.js!";
        event_manager.publish_reply(
            event,
            prepareEventData({
                error_message: error_message,
            }),
        );
        error(error_message, false);
        return;
    }

    try {
        if (event.data.remote_integration_session_id !== remote_integration_session_id) {
            return;
        }

        const function_name_raw = event.data.function_name;
        const function_name = FTRACK_RPC_FUNCTION_MAPPING[function_name_raw];

        if (function_name === undefined || function_name.length === 0) {
            const error_message =
                "[INTERNAL ERROR] No RPC function mapping defined for '" + function_name_raw + "'";
            event_manager.publish_reply(
                event,
                prepareEventData({
                    error_message: error_message,
                }),
            );
            error(error_message, false);
            return;
        }

        const fn = window.FTRACK_RPC_FUNCTIONS
            ? window.FTRACK_RPC_FUNCTIONS[function_name]
            : window[function_name];

        if (typeof fn !== "function") {
            const error_message =
                "[INTERNAL ERROR] RPC function not found: '" + function_name + "'";
            event_manager.publish_reply(
                event,
                prepareEventData({
                    error_message: error_message,
                }),
            );
            error(error_message, false);
            return;
        }

        const result = await fn.apply(null, event.data.args || []);

        event_manager.publish_reply(
            event,
            prepareEventData({
                result: result,
            }),
        );
    } catch (e) {
        const error_message =
            "[INTERNAL ERROR] Failed to run RPC call! " + e + " Details: " + e.stack;
        event_manager.publish_reply(
            event,
            prepareEventData({
                error_message: error_message,
            }),
        );
        error(error_message, false);
    }
}


function openContext() {
    if (!event_manager || !event_manager.session || !context_id || !project_id) {
        console.warn("[ftrack panel] Context URL is not available yet.");
        return;
    }

    const task_url =
        event_manager.session.serverUrl +
        "/#slideEntityId=" +
        context_id +
        "&slideEntityType=task&view=tasks&itemId=projects&entityId=" +
        project_id +
        "&entityType=show";
    shell.openExternal(task_url);
}


initializeIntegration();
