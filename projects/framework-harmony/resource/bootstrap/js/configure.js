/**
 * Harmony ftrack integration
 * 
 * Main JS plugin entry point
 *
 * Copyright (c) 2024 ftrack
 */
"use strict";

const INT32_SIZE = 4;
const _BASE_ = "ftrack.framework";

const REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC = _BASE_ + ".remote.integration.context.data";
// Sent back from standalone process to integration supplying context data.

const REMOTE_INTEGRATION_RUN_DIALOG_TOPIC = _BASE_ + ".remote.integration.run.dialog";
// Sent from remote integration to standalone process to run a dialog - launch tool.

const REMOTE_INTEGRATION_RPC_TOPIC = _BASE_ + ".remote.integration.rpc";
// Sent from standalone process to remote integration in order to run a function
// within JS and return the result


if (this['__packageFolder__']) {
    MessageLog.trace("[ftrack] Including utilities");
    include(__packageFolder__+"/ftrack/utils.js");

    info("Including harmony commands");
    include(__packageFolder__+"/ftrack/harmony_commands.js");

} else {
    // Menu/toolbar launch: (re)define the launch_<name> callbacks in
    // this evaluation's scope. app.integration can be absent right after
    // a scene switch (Harmony tore down the engine that created it);
    // guard so a stray evaluation no-ops instead of throwing.
    if (QCoreApplication.instance().integration) {
        QCoreApplication.instance().integration.createLaunchers(this);
    }
}

/*
* TCP client that dials out to the standalone framework process' RPC
* server. The server (the external Python process) outlives Harmony's
* Qt Script engine, so the RPC channel survives every scene switch:
* Harmony tears down the engine - and this socket - on each scene
* open/create/close and simply reconnects here (from configure() at
* launch and from the TB_scene* hooks afterwards).
*/
function TCPClient(host, port, integration) {

    // Parent the socket to the application (not this transient engine)
    // so the underlying C++ object is not tied to the engine's lifetime.
    this.socket = new QTcpSocket(QCoreApplication.instance());
    this.host = host;
    this.port = port;
    this.integration = integration;
    this.connected = false;
    this.blocksize = 0;

    this.connect = function()
    {
        this.blocksize = 0;
        this.socket.connected.connect(this, this.onConnected);
        this.socket.readyRead.connect(this, this.handleEvent);
        this.socket.disconnected.connect(this, this.onDisconnect);
        info("Connecting to ftrack RPC server @ " + this.host + ":" + this.port);
        this.socket.connectToHost(this.host, this.port);
    }

    this.onConnected = function() {
        info("Connected to ftrack RPC server @ " + this.host + ":" + this.port);
        this.blocksize = 0;
        this.connected = true;
    }

    this.prepareEvent = function(topic, event_data, source, in_reply_to_event) {
        event_data["integration_session_id"] = this.integration.harmony_session_id
        var result = {
            id: uuidv4(),
            topic: topic,
            data: event_data,
            source: source
        }
        if (in_reply_to_event != undefined) {
            result["in_reply_to_event"] = in_reply_to_event;
        }
        return result;
    }

    this.send = function(topic, event_data, in_reply_to_event) {
        try {
            var event = this.prepareEvent(topic, event_data, "harmony", in_reply_to_event);
            debug("Sending event: "+JSON.stringify(event));
            if (this.connected) {
                raw_event = JSON.stringify(event);

                var data = new QByteArray();

                out = new QDataStream(data, QIODevice.WriteOnly);
                out.setVersion(QDataStream.Qt_4_6);
                out.writeInt(0);

                data.append(raw_event);

                out.device().seek(0);
                out.writeInt(data.size() - 4);

                var written = this.socket.write(data);
                debug("Sent event "+JSON.stringify(raw_event)+" (length: " + written + ")");

                return true;
            } else {
                warning("Event hub not connected!");
                return false;
            }
        } catch(err) {
            warning("Failed to send event! "+err);
        }
    }

    this.handleEvent = function() {
        try
        {
            info("Receiving event... ");

            var stream = new QDataStream();
            stream.setDevice(this.socket);
            stream.setVersion(QDataStream.Qt_4_6);

            debug("Available bytes: " + this.socket.bytesAvailable());
            var i = 0;
            while (this.socket.bytesAvailable() > 0) {
                debug("Receiving event: " + i);

                if ( (this.blocksize == 0 && this.socket.bytesAvailable() >= INT32_SIZE) || (this.blocksize > 0 && this.socket.bytesAvailable() >= this.blocksize) ) {
                    this.blocksize = stream.readInt();
                    debug("Event number: " + i + ", block size: " + this.blocksize);
                }

                if (this.blocksize > 0 && this.socket.bytesAvailable() >= this.blocksize) {
                    var data = this.socket.read(this.blocksize);

                    // create the event
                    var raw_event = "";
                    for ( var j = 0; j < data.size(); j++)
                    {
                        if (data.at(j) >0 )
                        {
                            raw_event = raw_event.concat(String.fromCharCode(data.at(j)));
                        }
                    }
                    this.decodeAndProcessEvent(raw_event);
                    this.blocksize = 0;
                    i += 1;
                }
            }
        } catch(err) {
            warning("Failed to handle incoming event! "+err);
        }
    }

    this.decodeAndProcessEvent = function(raw_event) {
        debug("Decoding event: " + raw_event)
        try {
            var event = JSON.parse(raw_event)
            // Call event process in base extension
            this.integration.processEvent(event["topic"], event["data"], event["id"]);
        } catch (err) {
            warning("Failed to parse and have integration process event! "+err);
            return;
        }
    }

    this.onError = function(socket_error) {
        warning("An error occurred with the RPC server connection: " + socket_error.toString());
    }

    this.onDisconnect = function(socket_error) {
        info("Disconnected from ftrack RPC server.");
        this.connected = false;
    }

    this.close = function() {
        this.socket.abort();
    }
}


function HarmonyIntegration() {
    // The ftrack Harmony integration handler

    this.harmony_session_id = null;

    this.tcp_client = null;

    this.initialized = false;
    this.session = null;

    this.launchers = [];

    // Whether the ftrack toolbar and shortcut have been built for THIS
    // connection. A fresh HarmonyIntegration is created on every
    // (re)connect (see ftrackConnectIntegration), so this resets on each
    // scene switch - which is exactly what we want, because the toolbar
    // and shortcut do NOT survive a scene switch and must be rebuilt.
    this.ftrack_ui_built = false;

    /**
    * Initialize the integration, dial out to the standalone framework
    * process' RPC server and listen for incoming events.
    */
    this.initializeIntegration = function() {

        debug("Initializing integration");

        this.harmony_session_id = System.getenv("FTRACK_REMOTE_INTEGRATION_SESSION_ID");
        if (!this.harmony_session_id) {
            error("Missing FTRACK_REMOTE_INTEGRATION_SESSION_ID environment, cannot launch ftrack integration. Really launched from Connect?");
            return;
        }

        info('DCC session ID: '+this.harmony_session_id);

        // Dial out to the standalone process' RPC server. That server
        // outlives Harmony's Qt Script engine, so it is up whenever we
        // (re)connect after a scene switch.
        var port = parseInt(System.getenv("FTRACK_INTEGRATION_LISTEN_PORT"));
        this.tcp_client = new TCPClient("localhost", port, this);
        this.tcp_client.connect();

        var app = QCoreApplication.instance();
        // Best-effort only: registered from a transient engine, so this
        // may not fire. It is not load-bearing - the OS closes loopback
        // sockets on exit and a Harmony quit is handled by the process
        // watchdog in the standalone.
        app.aboutToQuit.connect(app, this.shutdown);

        this.initialized = true;
    }

    /**
    * Send event to standalone integration
    */
    this.sendEvent = function(topic, data, in_reply_to_event) {
        this.tcp_client.send(topic, data, in_reply_to_event);
    }

    /**
    * Process incoming event from standalone integration.
    */
    this.processEvent = function(topic, data, id) {
        info("Processing incoming '"+topic+"' event: "+JSON.stringify(data));
        if (topic === REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC) {
            // Incoming connection from standalone integration
            this.handleIntegrationContextDataCallback(topic, data, id);
            this.sendEvent(topic, {}, id); // Return reply
        } else if (topic === REMOTE_INTEGRATION_RPC_TOPIC) {
            this.handleRemoteIntegrationRPCCallback(topic, data, id);
        }
    }

    /**
    * Handle context data from standalone integration, build menus and notify
    * user extension of connection.
    */
    this.handleIntegrationContextDataCallback = function(topic, data, id) {
        info("Got context data from standalone integration, building menus.");
        this.launchers = data["launchers"];

        // Persist the launcher list as a plain JSON string on the
        // application: strings survive property round-trips across
        // script engines (objects come back as lossy copies), and the
        // scene-watch rebuild depends on it.
        QCoreApplication.instance().ftrack_launchers_json =
            JSON.stringify(this.launchers);

        // Menu items are dropped on every scene switch, so rebuild them
        // on every CONTEXT_DATA (i.e. on every (re)connection).
        ftrackRebuildMenus();

        // The toolbar and shortcut do NOT survive a scene switch (Harmony
        // tears them down along with the menu items), so they must be
        // rebuilt on each (re)connection - same trick as the menu. Guard
        // on the INSTANCE flag, not the persistent application: a fresh
        // HarmonyIntegration exists per (re)connect, so the flag is false
        // again after every scene switch (toolbar gets rebuilt), while a
        // second CONTEXT_DATA on the same connection won't stack a
        // duplicate. Stable ids ("ftrackToolbar"/"ftrackShortcut") also
        // make a re-add idempotent should the toolbar ever persist.
        if (this.ftrack_ui_built) {
            return;
        }

        var ftrackToolbar = new ScriptToolbarDef( {
            id           : "ftrackToolbar",
            text         : "ftrack",
            customizable : "false"
        } );

        for (var idx = 0; idx < this.launchers.length; idx++) {
            var launcher = this.launchers[idx];
            var name = launcher["name"];
            var label = launcher["label"];
            var action = "launch_"+name+" in ./configure.js";

            // Keyboard shortcut for the primary publish tool.
            if (name == "publish") {
                ScriptManager.addShortcut( {
                    id           : "ftrackShortcut",
                    text         : "ftrack "+label+" ...",
                    action       : action,
                    longDesc     : "ftrack integration",
                    order        : "256",
                    categoryId   : "ftrack",
                    categoryText : "Scripts"
                } );
            }

            // Toolbar button for the tool.
            ftrackToolbar.addButton( {
                text   : label,
                icon   : "ftrack.png",
                action : action
            } );
        }

        ScriptManager.addToolbar(ftrackToolbar);

        this.ftrack_ui_built = true;
    }

    /**
    * Create launchers for each tool in the integration, bind it to the global
    * script this context to facilitate menu callbacks.
    */
    this.createLaunchers = function(this_) {
        var launchers = this.launchers;
        if (!launchers || launchers.length === 0) {
            // Script-object properties read back through
            // QCoreApplication.instance() can be lossy copies across
            // script engines - fall back to the JSON string.
            try {
                launchers = JSON.parse(
                    QCoreApplication.instance().ftrack_launchers_json
                    || "[]"
                );
            } catch (err) {
                launchers = [];
            }
        }
        for (var idx = 0; idx < launchers.length; idx++) {
            // Bind each launcher in its own scope - with a plain `var`
            // loop every generated launch_<name> would close over the
            // last launcher, so all menu items would run the same tool.
            (function(launcher) {
                var name = launcher["name"];
                var dialog_name = launcher["dialog_name"];
                var options = launcher["options"];

                this_["launch_"+name] = function() {
                    var app = QCoreApplication.instance();
                    app.integration.sendEvent(
                        REMOTE_INTEGRATION_RUN_DIALOG_TOPIC,
                        {
                            "name": name,
                            "dialog_name": dialog_name,
                            "options": options
                        }
                    )
                }
            })(launchers[idx]);
        }
    }

    /**
    * Handle RPC calls from standalone process - run function with arguments
    * supplied in event and return the result
    */
    this.handleRemoteIntegrationRPCCallback = function(topic, data, id) {
        /* .*/
        try {
            var function_name = data.function_name;

            if (function_name === undefined || function_name.length === 0) {
                this.sendEvent(topic, {
                    "error_message": "No RCP function name given!"
                }, id);
                return;
            }
            // Build args, quote strings
            var s_args = '';
            for (var idx = 0; idx < data.args.length; idx++) {
                var value = data.args[idx];
                if (typeof value === 'string')
                    value = '"' + value + '"';
                s_args += (s_args.length>0?",":"") + value;
            }

            info("Running RPC call: "+function_name+"("+s_args+")");
            var result = eval(function_name+'('+s_args+')');

            try {
                // String is the evalScript type, decode
                this.sendEvent(topic, {
                    "result": result
                }, id);
            } catch (e) {
                error_message = "[INTERNAL ERROR] Failed to convert RPC call result '"+result+"'! "+e+" Details: "+e.stack;
                this.sendEvent(topic, {
                    "error_message": error_message
                }, id);
                error(error_message);
            }
        } catch (e) {
            error_message = "[INTERNAL ERROR] Failed to run RPC call! "+e+" Details: "+e.stack;
            this.sendEvent(topic, {
                "error_message": error_message
            }, id);
            error(error_message);
        }
    }

    /**
    * Get the current scene path
    */
    this.getScenePath = function() {
        var scene_path = scene.currentProjectPath();
        return scene_path;
    }

    /**
    * Get the current start frame
    */
    this.getStartFrame = function(data) {
        var start_frame = scene.getStartFrame();
        return start_frame;
    }

    /**
    * Get the current end frame
    */
    this.getEndFrame = function(data) {
        var end_frame = scene.getStopFrame();
        return end_frame;
    }

    /**
    * Run on shutdown - drop the RPC connection. Best-effort (see
    * initializeIntegration): the standalone owns real shutdown via its
    * process watchdog.
    */
    this.shutdown = function() {
        warning("Shutting down ftrack integration.")
        this.tcp_client.socket.abort();
    }
}

/**
* (Re-)register the ftrack menu entries, e.g. after a scene switch
* rebuilt the menu bar. Reads the launcher list from the JSON string
* stored on the application by the context-data handshake, so it works
* from any script engine. Also callable through RPC.
*
* Grouping: Harmony's ScriptManager can only add items to existing
* menus; a real "ftrack" submenu or a custom top-level menu needs
* overriding the whole menus.xml, which is version-brittle (a
* hierarchical targetMenuId like "File/ftrack" does not render on
* Harmony 27). The entries go at the end of the File menu, where they
* appear adjacent after a separator (the Windows menu scatters script
* items).
*
* @returns {boolean} True if menu entries were registered
*/
function ftrackRebuildMenus() {
    var launchers = [];
    try {
        launchers = JSON.parse(
            QCoreApplication.instance().ftrack_launchers_json || "[]"
        );
    } catch (err) {
        warning("Could not read ftrack launchers: " + err);
        return false;
    }
    for (var idx = 0; idx < launchers.length; idx++) {
        var launcher = launchers[idx];
        var name = launcher["name"];
        var label = launcher["label"];

        ScriptManager.addMenuItem( {
            targetMenuId : "File",
            id           : "ftrackMenu"+name+"ID",
            icon         : "ftrack.png",
            text         : "ftrack "+label,
            action       : "launch_"+name+" in ./configure.js"
        } );
    }
    return launchers.length > 0;
}

/**
* (Re-)connect the ftrack integration to the standalone process' RPC
* server. Harmony destroys the Qt Script engine - and with it this
* engine's socket wrapper - on every scene open/create/close, and does
* NOT re-invoke configure(). The TB_scene* hooks call this (after
* re-including this file) to dial the still-listening server again; the
* server re-sends its launcher context data so the ftrack menu, toolbar
* and shortcut are all rebuilt (none of them survive a scene switch).
* The listen port and session id come from the process environment,
* which persists for Harmony's whole lifetime.
*
* Always (re)connects. Harmony tears down the Qt Script engine - and
* this engine's socket - on every scene switch, so a fresh dial is
* required each time. We must NOT short-circuit on a previous
* app.integration: after a scene switch it is a dead cross-engine copy
* whose `connected` flag reads back stale-true, which would block every
* reconnect. The standalone server aborts the stale socket when the new
* one connects, and the menu/toolbar re-registration is idempotent
* (stable ids), so re-connecting is safe.
*/
function ftrackConnectIntegration() {
    var app = QCoreApplication.instance();

    app.integration = new HarmonyIntegration();
    app.integration.initializeIntegration();
}

function configure(packageFolder, packageName)
{
    if (about.isPaintMode())
        return;

    ftrackConnectIntegration();
}

function init()
{
    info("ftrack Framework Harmony integration INIT");
}

// `exports` only exists when Harmony loads this file as a package. The
// TB_scene* hooks re-include this file from a plain script scope (no
// module system) to reuse ftrackConnectIntegration(), so guard the
// assignments or the include would throw a ReferenceError.
if (typeof exports !== "undefined") {
    exports.configure = configure;
    exports.init = init;
}