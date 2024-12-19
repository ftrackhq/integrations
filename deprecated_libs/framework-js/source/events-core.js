/*
 ftrack framework Javascript core

 Copyright (c) 2024 ftrack
*/

// Events

class EventManager {
    /*
    * ftrack Framework JS event manager
    */

    constructor(session) {
        this._session = session;

        this.publish = new Publish(this);
        this.subscribe = new Subscribe(this);
    }

    get session() {
        // Return the session
        return this._session;
    }

    _subscribe(topic, callback_fn) {
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

    _publish(topic, data) {
        let event = new ftrack.Event(topic, data);
        this.session.eventHub.publish(event);
    }

    publish_reply(source_event, data) {
        this.session.eventHub.publishReply(source_event, data);
    }
};


class Publish {
    /*
    * Class with all the events published by the JS framework
    */

    constructor(event_manager) {
        this._event_manager = event_manager;
    }

    get event_manager() {
        // Return the session
        return this._event_manager;
    }

    discover_remote_integration(data) {
        let event_topic = DISCOVER_REMOTE_INTEGRATION_TOPIC;
        this.event_manager._publish(event_topic, data);
    }

    remote_integration_run_dialog(data) {
        let event_topic = REMOTE_INTEGRATION_RUN_DIALOG_TOPIC;
        this.event_manager._publish(event_topic, data);
    }

};

class Subscribe {
    /*
    * Class with all the events subscribed by the JS framework
    */

    constructor(event_manager) {
        this._event_manager = event_manager;
    }

    get event_manager() {
        // Return the session
        return this._event_manager;
    }

    discover_remote_integration(callback) {
        let event_topic = DISCOVER_REMOTE_INTEGRATION_TOPIC;
        this.event_manager._subscribe(event_topic, callback);
    }

    integration_context_data(callback) {
        let event_topic = REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC;
        this.event_manager._subscribe(event_topic, callback);
    }

    remote_integration_rpc(callback) {
        let event_topic = REMOTE_INTEGRATION_RPC_TOPIC;
        this.event_manager._subscribe(event_topic, callback);
    }

};


