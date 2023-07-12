# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import threading

import logging
import ftrack_api
from ftrack_framework_core import constants
import uuid

logger = logging.getLogger(__name__)


class _EventHubThread(threading.Thread):
    '''Listen for events from ftrack's event hub.'''

    def __repr__(self):
        return "<{0}:{1}>".format(self.__class__.__name__, self.name)

    def __init__(self, session):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        _name = str(hash(session))
        super(_EventHubThread, self).__init__(name=_name)
        self.logger.debug('Name set for the thread: {}'.format(_name))
        self._session = session

    def start(self):
        '''Start thread for *_session*.'''
        self.logger.debug(
            'starting event hub thread for session {}'.format(self._session)
        )
        super(_EventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self.logger.debug(
            'hub thread started for session {}'.format(self._session)
        )
        self._session.event_hub.wait()


class EventManager(object):
    '''Manages the events handling.'''

    def __repr__(self):
        return '<EventManager:{}:{}>'.format(self.mode, self.id)

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    @property
    def id(self):
        return uuid.uuid4().hex

    @property
    def session(self):
        return self._session

    @property
    def connected(self):
        _connected = False
        try:
            _connected = self.session.event_hub.connected
        except Exception as e:
            self.logger.error(
                "Error checking event hub connected {}".format(e)
            )
        return _connected

    @property
    def mode(self):
        return self._mode

    @property
    def events(self):
        return self._events_class

    def _connect(self):
        # If is not already connected, connect to event hub.
        while not self.connected:
            self.session.event_hub.connect()

    def _wait(self):
        for thread in threading.enumerate():
            if thread.getName() == str(hash(self.session)):
                self._event_hub_thread = thread
                break
        if not self._event_hub_thread:
            # self.logger.debug('Initializing new hub thread {}'.format(self))
            self._event_hub_thread = _EventHubThread(self.session)

        if not self._event_hub_thread.is_alive():
            # self.logger.debug('Starting new hub thread for {}'.format(self))
            self._event_hub_thread.start()

    def __init__(self, session, mode=constants.LOCAL_EVENT_MODE):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_hub_thread = None
        self._mode = mode
        self._session = session
        if mode == constants.REMOTE_EVENT_MODE:
            # TODO: Bring this back when API event hub properly can differentiate between local and remote mode
            self._connect()
            self._wait()

        self._events_class = Events(self)

        # self.logger.debug('Initialising {}'.format(self))

    def publish(self, event, callback=None, mode=None):
        '''Emit *event* and provide *callback* function.'''

        mode = mode or self.mode
        # self.logger.debug(
        #     'Publishing event topic {} in {} mode'.format(
        #         event.get('topic'), mode
        #     )
        # )
        if mode is constants.LOCAL_EVENT_MODE:
            result = self.session.event_hub.publish(
                event,
                synchronous=True,
            )

            if result:
                result = result[0]

            # Mock async event reply.
            new_event = ftrack_api.event.base.Event(
                topic='ftrack.meta.reply',
                data=result,
                in_reply_to_event=event['id'],
            )

            if callback:
                callback(new_event)

        else:
            self.session.event_hub.publish(event, on_reply=callback)

    def subscribe(self, topic, callback):
        subscribe_id = self.session.event_hub.subscribe('topic={}'.format(topic), callback)
        return subscribe_id

    def available_framework_events(self):
        pass


class Events(object):

    @property
    def event_manager(self):
        return self._event_manager

    @property
    def publish(self):
        return self._publish_class

    @property
    def subscribe(self):
        return self._subscription_class

    def __init__(self, event_manager):
        super(Events, self).__init__()
        self._event_manager = event_manager
        self._publish_class = Publish(self.event_manager)
        self._subscription_class = Subscribe(self.event_manager)

    def list(self):
        #TODO: retrun all available events
        pass

# TODO: all pipeline events should be renamed to framework events, including
#  the structure: data/pipeline/<data> should be renamed to data/framework/<data>
#  or directly data/<data>


class Publish(object):

    @property
    def event_manager(self):
        return self._event_manager

    def __init__(self, event_manager):
        super(Publish, self).__init__()
        self._event_manager = event_manager

    def _publish_event(self, event_topic, data, callback):
        event = ftrack_api.event.base.Event(topic=event_topic, data=data)
        self.event_manager.publish(event, callback=callback)

    def discover_host(self, callback=None):
        topic = constants.DISCOVER_HOST_TOPIC
        self._publish_event(topic, callback)

    def host_run_definition(self, host_id, definition, engine_type, callback=None):
        data = {
            'host_id': host_id,
            'definition': definition,
            'engine_type': engine_type,
        }
        event_topic = constants.HOST_RUN_DEFINITION_TOPIC
        self._publish_event(event_topic, data, callback)

    def host_context_changed(self, host_id, context_id, callback=None):
        data = {
            'host_id': host_id,
            'context_id': context_id,
        }
        event_topic = constants.HOST_CONTEXT_CHANGED_TOPIC
        self._publish_event(event_topic, data, callback)

    def launch_client_widget(self, host_id, widget_name, source=None, callback=None):
        '''Send a widget launch event, to be picked up by DCC.'''
        # TODO: call this from a new launch_assembler method in the opener
        #  client or in any other place. The data needed is like the following:
        data = {
            'host_id': host_id,
            'name': widget_name,
            'source': source,
        }

        event_topic = constants.CLIENT_LAUNCH_WIDGET_TOPIC
        self._publish_event(event_topic, data, callback)


class Subscribe(object):

    @property
    def event_manager(self):
        return self._event_manager

    def __init__(self, event_manager):
        super(Subscribe, self).__init__()
        self._event_manager = event_manager

    def _subscribe_event(self, event_topic, callback):
        return self.event_manager.subscribe(event_topic, callback=callback)

    def discover_host(self, callback):
        topic = constants.DISCOVER_HOST_TOPIC
        return self._subscribe_event(topic, callback)
    def host_run_definition(self, host_id, callback=None):
        event_topic = '{} and data.host_id={}'.format(
            constants.HOST_RUN_DEFINITION_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_context_changed(self, host_id, callback=None):
        event_topic = '{} and data.host_id={}'.format(
            constants.HOST_CONTEXT_CHANGED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def launch_client_widget(self, host_id, callback=None):
        event_topic = '{} and data.host_id={}'.format(
            constants.CLIENT_LAUNCH_WIDGET_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

