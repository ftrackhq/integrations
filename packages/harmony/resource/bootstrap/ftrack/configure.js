"use strict";

//import 'ftrack.0.7.2.min.js';

// Event commands

const TOPIC_CLIENT_LAUNCH = "ftrack.pipeline.client.launch";
const TOPIC_PING = "ftrack.pipeline.ping";
const TOPIC_RENDER_DO = "ftrack.pipeline.render.do";
const TOPIC_RENDER_FINISHED = "ftrack.pipeline.render.finished";

// Misc

const INT32_SIZE = 4;
const DEBUG = true;

// Logging

function info(s) {
    MessageLog.trace("[ftrack] "+s);
}

function warning(s) {
    info("WARNING: "+s);
}

function debug(s) {
    if (DEBUG) 
        info("//DEBUG// "+s);
}

function uuidv4() {
    var d = new Date().getTime();//Timestamp
    var d2 = ((typeof performance !== 'undefined') && performance.now && (performance.now()*1000)) || 0;//Time in microseconds since page-load or 0 if unsupported
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16;//random number between 0 and 16
        if(d > 0){//Use timestamp until depleted
            r = (d + r)%16 | 0;
            d = Math.floor(d/16);
        } else {//Use microseconds since page-load if supported
            r = (d2 + r)%16 | 0;
            d2 = Math.floor(d2/16);
        }
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}

function EventHub(host, port, integration) {
    // ftrack event hub implementation
    // Spawns an scaled down event hub listener listening on local TCP port.

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
            this.socket.newConnection.connect(this, this.newConnection);
            return true;
        }
        else
        {
            this.listening = false;
            warning("Local Server could not start! " + this.host.toString() + ":" + this.port);
            return false;
        }
    }

    this.newConnection = function() {
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

                debug("Connection state: " + state);
                info("Client connected: " + this.connection.toString()+ " (state: "+state+")");

                this.connected = true; 

                // Send a ping to know comms are working
                this.send(TOPIC_PING, {})
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
        return {
            id: uuidv4(),
            topic: topic,
            data: event_data,
            source: source,
            in_reply_to_event: in_reply_to_event
        }
    }

    this.send = function(topic, event, in_reply_to_event) {
        try
        {
            event = this.prepareEvent(topic, event, "harmony", in_reply_to_event);
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
                    i+=1;
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
            event = JSON.parse(raw_event)
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

function HarmonyIntegration() {
    // The ftrack Harmony integration handler

    this.harmony_session_id = null;

    this.initialized = false;
    this.session = null;

    this.bootstrap = function() {
        this.createLauncher();
        this.spawnIntegration();
    }

    this.createLauncher = function() {
        // Create integration menu launcher

        //---------------------------
        //Create Shortcuts
        ScriptManager.addShortcut( { id       : "ftrackShortcut",
                                   text     : "ftrack Menu ...",
                                   action   : "showMenu in ./configure.js",
                                   longDesc : "Starts the ftrack integration",
                                   order    : "256",
                                   categoryId   : "ftrack", 
                                   categoryText : "Scripts" } );
      
        //---------------------------
        //Create Menu items
        ScriptManager.addMenuItem( { targetMenuId : "Windows",
                                   id           : "ftrackMenuID",
                                   icon     : "ftrack.png",
                                   text         : "ftrack",
                                   action       : "showMenu in ./configure.js",
                                   shortcut     : "ftrackShortcut" } );

        //---------------------------
        //Create Toolbar
        var ftrackToolbar = new ScriptToolbarDef( { id          : "ftrackToolbar",
                                                   text        : "ftrack",
                                                   customizable: "false" } );
      
        ftrackToolbar.addButton( { text     : "ftrack",
                                      icon     : "ftrack.png",
                                      action   : "showMenu in ./configure.js" ,
                                      shortcut : "ftrackShortcut" } );

        ScriptManager.addToolbar(ftrackToolbar);
    }

    this.spawnIntegration = function() {
        // TODO: Spawn integration in separate process
        this.harmony_session_id = System.getenv("FTRACK_INTEGRATION_SESSION_ID");
        if (!this.harmony_session_id) {
            // DEV
            this.harmony_session_id = "c06cda19-001a-40d2-b2f3-13b37db270f6"; 
        }

        info('Session ID: '+this.harmony_session_id);

        // Spawn event hub and start listening to events

        this.event_hub = new EventHub("localhost", System.getenv("FTRACK_INTEGRATION_LISTEN_PORT"), this);
        
        this.event_hub.start();

        /*session = new ftrack.Session(
            'https://ftrack-integrations.ftrackapp.com',
            'henrik.norin@ftrack.com',
            'YWNkMTJjY2ItMmYzYy00ZmJjLWI3NWMtNDdiMWFiZWFkMmQxOjo0ZTQ1MDEyNy1hM2QzLTRkMDEtYWQ5NS02ZGNjN2E4MWE0ZWU', 
            { autoConnectEventHub: true }
        );*/

        this.initialized = true;
    }

    this.showMenu = function() {
        // Send the show menu event
        var x_coord = QCursor.pos().x();
        var y_coord = QCursor.pos().y();

        this.event_hub.send(TOPIC_CLIENT_LAUNCH,{
            pipeline: {
                name: 'menu',
                source: '',
                x:x_coord, 
                y:y_coord
            }
            
        });
        /*
        var event = new ftrack.Event('ftrack.pipeline.client.launch', {
            pipeline: {
                integration_session_id: harmony_session_id,
                name: 'publisher',
                source: ''
            }
        })
        info("Publishing menu spawn event: "+JSON.stringify(event)+"<br>");
        this.session.eventHub.publish(event); */
    }

    this.get_scene_path = function() {
        var scene_path = scene.currentProjectPath();
        return scene_path;
    }

    this.get_start_frame = function(data)
    {
        var start_frame = scene.getStartFrame();
        return start_frame;
    }

    this.get_end_frame = function(data)
    {
        var end_frame = scene.getStopFrame();
        return end_frame;
    }


    this.processEvent = function(topic, event_data, id) {
        info("Processing incoming '"+topic+"' event: "+JSON.stringify(event_data));
        pipeline_data = event_data["pipeline"]
        if (topic === TOPIC_PING) {
            info("Ignoring incoming ping event from standalone integration");
        } else if (topic === TOPIC_RENDER_DO) {
            if (pipeline_data === undefined) {
                warning("Cannot render, no pipeline event data supplied!");
                return;
            }
            start = this.get_start_frame()
            if (pipeline_data.start_frame != undefined)
                start_frame = pipeline_data.start_frame;
            end = this.get_end_frame()
            if (pipeline_data.end_frame != undefined)
                end_frame = pipeline_data.end_frame;
            destination_path = pipeline_data.destination_path;
            prefix = pipeline_data.prefix;
            extension = pipeline_data.extension;
            info("(render) Rendering '"+this.get_scene_path()+"', frames: "+start+"-"+end+" > "+destination_path)
        
            function frameReady(frame, celImage)
            {
              info("(render) Frame " + frame + " Ready.");
              // Save the image here.
              celImage.imageFile(destination_path + prefix + "." + frame + extension);
            }
            function renderFinished()
            {
              MessageBox.information("Render Finished");
            }
            render.renderFinished.connect(renderFinished);
            render.frameReady.connect(frameReady);
            render.setRenderDisplay("Top/Display");
            render.renderSceneAll();
            render.renderFinished.disconnect(renderFinished);
            render.frameReady.disconnect(frameReady);

            info("(render)  Render finished");

            this.event_hub.send(TOPIC_RENDER_FINISHED, {}, id)
        }
    }
}



function configure(packageFolder, packageName)
{
    if (about.isPaintMode())
        return;

    var app = QCoreApplication.instance();

    app.integration = new HarmonyIntegration();
    app.integration.bootstrap();
}

function showMenu()
{
    var app = QCoreApplication.instance();

    if (app.integration != undefined) {
        app.integration.showMenu();
    } else {
        warning("Can't show menu - not created yet!");
    }
}

function init()
{
    info("Connect Harmony integration INIT");
}


exports.configure = configure;
exports.init = init;