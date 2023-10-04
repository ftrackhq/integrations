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
    }

    get session() {
        // Return the session
        return this._session;
    }

    subscribe(topic, callback_fn) {
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

    publish(topic, data, reply_to_event) {
        let event = new ftrack.Event(topic, data);
        if (reply_to_event !== undefined) {
            event.in_reply_to_event = in_reply_to_event;
        }
        this.session.eventHub.publish(event);
    }
};

