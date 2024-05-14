/**
 * Harmony ftrack integration
 * 
 * Utilities and helper classes
 */

const INT32_SIZE = 4;
const DEBUG = true;

// Logging

function info(s) {
    MessageLog.trace("[ftrack] "+s);
}

function warning(s) {
    info("WARNING: "+s);
}

function error(s) {
    info("ERROR: "+s);
}

function debug(s) {
    if (DEBUG) {
        info("//DEBUG// "+s);
    }
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
        return {
            id: uuidv4(),
            topic: topic,
            data: event_data,
            source: source,
            in_reply_to_event: in_reply_to_event
        }
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
