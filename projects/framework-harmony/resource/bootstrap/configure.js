/**
 * Harmony ftrack integration
 * 
 * Main JS entry point
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

/*MessageLog.trace("===========================================================");
for (var property in this) {
    try {
        MessageLog.trace(property + ": " + this[property]);
    } catch (error) {
        MessageLog.trace(error.stack+"");
    }
}*/

if (this['__packageFolder__']) {
    MessageLog.trace("[ftrack] Including utilities");
    include(__packageFolder__+"/ftrack/harmony-utils.js");

    info("Including base extensions");
    include(__packageFolder__+"/ftrack/harmony-extensions.js");

    info("Including user extensions");
    include(__packageFolder__+"/ftrack/harmony-user-extensions.js");
} else {
    // Menu launch, create launchers
    QCoreApplication.instance().integration.createLaunchers(this);
}


/*
var funcName = "testFunc";
var args = "'Hello'";

eval(funcName + "(" + args + ")");
*/




// Event commands


/*const TOPIC_CLIENT_LAUNCH = "ftrack.pipeline.client.launch";
const TOPIC_PING = "ftrack.pipeline.ping";
const TOPIC_RENDER_DO = "ftrack.pipeline.render.do";
const TOPIC_RENDER_FINISHED = "ftrack.pipeline.render.finished";

const TOPIC_SHUTDOWN = "ftrack.pipeline.shutdown";*/



/*
* TCP server implementation acting as a scaled down event hub, that
* standalone framework process can connect to and communicate with.
*/
function TCPServer(host, port, integration) {

    this.socket = new QTcpServer(this);
    this.address = host;
    this.host = new QHostAddress(host);
    this.port = port;
    this.integration = integration;
    this.listening = false;
    this.connected = false;
    this.connection = null;
    this.blocksize;

    this.start = function()
    {
        this.active = false;
        this.connection = null;
        this.blocksize = 0;

        if (this.socket.listen(this.host, this.port))
        {
            info("Local event hub server started @ " + this.address + ":" + this.port);
            this.listening  = true;
            this.socket.newConnection.connect(this, this.handleIncomingConnection);
            return true;
        }
        else
        {
            this.listening = false;
            warning("Local Server could not start! " + this.host.toString() + ":" + this.port);
            return false;
        }
    }

    this.handleIncomingConnection = function() {
        info("New incoming connection");
        try
        {
            if (this.socket.hasPendingConnections())
            {
                this.connection = this.socket.nextPendingConnection();

                var state = this.connection.state();

                this.connection.readyRead.connect(this, this.handleEvent);

                //this.connection.error.connect(this, this.onError);

                this.connection.disconnected.connect(this, this.onDisconnect);

                info("Client connected: " + this.connection.toString()+ " (state: "+state+")");

                this.connected = true;

            }
            else
            {
                warning("No pending connections! %s" % this.connection.toString());
            }
        } catch(err)
        {
            warning("Failed to accept new connection! "+err);
        }
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
        try
        {
            event = this.prepareEvent(topic, event_data, "harmony", in_reply_to_event);
            debug("Sending event: "+JSON.stringify(event));
            if (this.connected) {
                raw_event = JSON.stringify(event);

                var data = new QByteArray();

                outstr = new QDataStream(data, QIODevice.WriteOnly);
                outstr.setVersion(QDataStream.Qt_4_6);
                outstr.writeInt(0);

                data.append(raw_event);

                outstr.device().seek(0);
                outstr.writeInt(data.size() - 4);

                var written = this.connection.write(data);
                debug("Sent event "+JSON.stringify(raw_event)+" (length: " + written + ")");

                return true;
            } else {
                warning("Event hub not connected!");
                return false;
            }
        } catch(err)
        {
            warning("Failed to send event! "+err);
        }
    }

    this.handleEvent = function() {
        try
        {
            info("Receiving event... ");

            var stream = new QDataStream();
            stream.setDevice(this.connection);
            stream.setVersion(QDataStream.Qt_4_6);

            debug("Available bytes: " + this.connection.bytesAvailable());
            var i = 0;
            while (this.connection.bytesAvailable() > 0)
            {
                debug("Receiving event: " + i);

                if ( (this.blocksize == 0 && this.connection.bytesAvailable() >= INT32_SIZE) || (this.blocksize > 0 && this.connection.bytesAvailable() >= this.blocksize) )
                {
                    this.blocksize = stream.readInt();
                    debug("Event number: " + i + ", block size: " + this.blocksize);
                }

                if (this.blocksize > 0 && this.connection.bytesAvailable() >= this.blocksize)
                {
                    var data = this.connection.read(this.blocksize);

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
        } catch(err)
        {
            warning("Failed to handle incoming event! "+err);
        }
    }

    this.decodeAndProcessEvent = function(raw_event) {
        debug("Decoding event: " + raw_event)
        try
        {
            var event = JSON.parse(raw_event)
            // Call event process in base extension
            this.integration.processEvent(event["topic"], event["data"], event["id"]);
        }
        catch(err)
        {
            warning("Failed to parse and process event! "+err);
            return;
        }
    }

    this.onError = function(socket_error)
    {
        warning("An error occurred with the event hub connection: " + socket_error.toString());
    }

    this.onDisconnect = function(socket_error)
    {
        info("Client disconnected.");
        this.connection = null;
        this.connected = false;
    }

    this.close = function()
    {
        this.listening = false;
        this.socket.close()
    }


}


function HarmonyIntegration(temp_path) {
    // The ftrack Harmony integration handler

    this.temp_path = temp_path;
    this.harmony_session_id = null;

    this._tcp_server = null;

    this.initialized = false;
    this.session = null;

    this.launchers = [];

    this.bootstrap = function() {
        this.spawnIntegration();
        var app = QCoreApplication.instance();
        app.aboutToQuit.connect(app, this.shutdown);
    }

    this.spawnIntegration = function() {

        debug("spawnIntegration()");

        this.harmony_session_id = System.getenv("FTRACK_REMOTE_INTEGRATION_SESSION_ID");
        if (!this.harmony_session_id) {
            error("Missing FTRACK_REMOTE_INTEGRATION_SESSION_ID environment, cannot launch ftrack integration. Really launched from Connect?");
            return;
        }

        info('Session ID: '+this.harmony_session_id);

        // Spawn TCP server and start listening to events

        var port = parseInt(System.getenv("FTRACK_INTEGRATION_LISTEN_PORT"));
        this._tcp_server = new TCPServer("localhost", port, this);
        this._tcp_server.start();

        this.initialized = true;
    }

    this.sendEvent = function(topic, data, in_reply_to_event) {
        this._tcp_server.send(topic, data, in_reply_to_event);
    }

    this.processEvent = function(topic, data, id) {
        info("Processing incoming '"+topic+"' event: "+JSON.stringify(data));
        if (topic === REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC) {
            // Incoming connection from standalone integration
            this.handleIntegrationContextDataCallback(topic, data, id);
            this.sendEvent(topic, {}, id); // Return reply
        } else if (topic === REMOTE_INTEGRATION_RPC_TOPIC) {
            this.handleRemoteIntegrationRPCCallback(topic, data, id);
        } else {
            // Have extension process event
            processEvent(integration, topic, data, id);
        }
    }

    this.handleIntegrationContextDataCallback = function(topic, data, id) {
        info("Got context data from standalone integration, building menus.");
        this.launchers = data["panel_launchers"];

        for (var idx = 0; idx < this.launchers.length; idx++) {
            var launcher = this.launchers[idx];
            var name = launcher["name"];
            var label = launcher["label"];

            // Add menu item, and create shortcut if it is the publish tool
            this.addMenuItem(name, label, name == "publish");
        }
    }

    this.addMenuItem = function(name, label, add_shortcut) {
        //---------------------------
        //Create Menu item

        //action = "launchTool('"+name+"') in ./actions.js";
        action = "launch_"+name+" in ./configure.js";
        payload = {
            targetMenuId : "Windows",
            id           : "ftrackMenu"+name+"ID",
            icon         : "ftrack.png",
            text         : "ftrack "+label,
            action       : action,
            shortcut     : "ftrackShortcut"
        }
        if (add_shortcut) {
            payload["shortcut"] = "ftrackShortcut";

            //---------------------------
            // Create Shortcuts
            ScriptManager.addShortcut( { id       : "ftrackShortcut",
                                       text     : "ftrack Menu ...",
                                       action   : action,
                                       longDesc : "ftrack integration",
                                       order    : "256",
                                       categoryId   : "ftrack",
                                       categoryText : "Scripts" } );

            //---------------------------
            // Create Toolbar
            var ftrackToolbar = new ScriptToolbarDef( { id          : "ftrackToolbar",
                                                       text        : "ftrack",
                                                       customizable: "false" } );

            ftrackToolbar.addButton( { text     : "ftrack",
                                          icon     : "ftrack.png",
                                          action   : action ,
                                          shortcut : "ftrackShortcut" } );

            ScriptManager.addToolbar(ftrackToolbar);
        }
        ScriptManager.addMenuItem( payload );
    }

    this.createLaunchers = function(this_) {
        for (var idx = 0; idx < this.launchers.length; idx++) {
            var launcher = this.launchers[idx];
            var name = launcher["name"];
            var label = launcher["label"];
            var dialog_name = launcher["dialog_name"];
            var tool_configs = launcher["options"]["tool_configs"];

            this_["launch_"+name] = function() {
                var app = QCoreApplication.instance();
                app.integration.sendEvent(
                    REMOTE_INTEGRATION_RUN_DIALOG_TOPIC,
                    {
                        "dialog_name": dialog_name,
                        "tool_configs": tool_configs
                    }
                )
            }
        }
    }

    this.launchTool = function(tool_name) {
        // Find dialog by *tool_name* and launch it
        var dialog_name = undefined, tool_configs = undefined;
        for (var idx = 0; idx < this.launchers.length; idx++) {
            var launcher = this.launchers[idx];
            if (launcher.name == tool_name) {
                dialog_name = launcher["dialog_name"];
                tool_configs = launcher["options"]["tool_configs"];
                break;
            }
        }

        this.sendEvent(
            REMOTE_INTEGRATION_RUN_DIALOG_TOPIC,
            {
                "dialog_name": dialog_name,
                "tool_configs": tool_configs
            }
        )
    }

    this.handleRemoteIntegrationRPCCallback = function(topic, data, id) {
        /* Handle RPC calls from standalone process - run function with arguments
            supplied in event and return the result.*/
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

    this.getScenePath = function() {
        var scene_path = scene.currentProjectPath();
        return scene_path;
    }

    this.getStartFrame = function(data)
    {
        var start_frame = scene.getStartFrame();
        return start_frame;
    }

    this.getEndFrame = function(data)
    {
        var end_frame = scene.getStopFrame();
        return end_frame;
    }

    this.shutdown = function() {
        warning("Shutting down ftrack integration.")
        // terminate tcp server
        this._tcp_server.close();
    }
}

function configure(packageFolder, packageName)
{
    if (about.isPaintMode())
        return;

    var app = QCoreApplication.instance();

    app.integration = new HarmonyIntegration(System.getenv("TMPDIR"));
    app.integration.bootstrap();
}

function init()
{
    info("ftrack Framework Harmony integration INIT");
}

exports.configure = configure;
exports.init = init;