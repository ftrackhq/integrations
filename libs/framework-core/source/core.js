/*
 ftrack framework Javascript core

 Copyright (c) 2014-2023 ftrack
*/

// Events

class EventManager {

    constructor(session, adobe_id) {
        this._session = session;
        this._adobe_id = adobe_id;
    }

    get session() {
        return this._session;
    }

    get adobe_id() {
        return this._adobe_id;
    }

    static createEvent(topic, framework_data) {
        framework_data.integration_session_id = adobe_id;
        let event = new ftrack.Event(topic, framework_data);
        return event;
    }

    subscribe(topic, callback_fn) {
        this.session.eventHub.subscribe("topic="+topic, this.handle_event.bind(
            this, callback_fn
        ));
    }

    handle_event(callback_fn, event) {

        if (event.source == undefined || event.data == undefined ||
            event.source.applicationId === 'ftrack.api.javascript' ||
            event.data.integration_session_id == undefined ||
            event.data.integration_session_id != this.adobe_id) {
            return;
        }

        console.log('(HUB) Received event from standalone process: ' + JSON.stringify(event));

        callback_fn(event);
    }

    publish(topic, framework_data, reply_to_event) {
        if (reply_to_event !== undefined) {
            framework_data.reply_to_event = reply_to_event;
        }
        let event = this.createEvent(topic, framework_data);
        console.log("Publishing event: "+JSON.stringify(event));
        this.session.eventHub.publish(event);
    }
};

