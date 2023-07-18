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
    def publish(self):
        '''
        Property to call the Publish class with all the predefined events used
        in the framework
        '''
        return self._publish_class

    @property
    def subscribe(self):
        '''
        Property to call the Subscribe class with all the predefined events used
        in the framework
        '''
        return self._subscribe_class

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

        # Initialize Publish and subscrive classes to be able to provide
        # predefined events.
        self._publish_class = Publish(self)
        self._subscribe_class = Subscribe(self)

        # self.logger.debug('Initialising {}'.format(self))

    def _publish(self, event, callback=None, mode=None):
        '''Emit *event* and provide *callback* function.'''

        mode = mode or self.mode

        if mode is constants.LOCAL_EVENT_MODE:
            result = self.session.event_hub.publish(
                event,
                synchronous=True,
            )

            if result:
                # TODO: this is to receive answers from all the suscribers. Maybe add an argument all_answers or just the first one.
                result = result#[0]

            # Mock async event reply.
            new_event = ftrack_api.event.base.Event(
                topic='ftrack.meta.reply',
                data=result,
                in_reply_to_event=event['id'],
            )

            if callback:
                callback(new_event)

            return result

        else:
            self.session.event_hub.publish(event, on_reply=callback)

    def _subscribe(self, topic, callback):
        subscribe_id = self.session.event_hub.subscribe('topic={}'.format(topic), callback)
        return subscribe_id

    def available_framework_events(self):
        pass


class Publish(object):
    '''Class with all the events published by the framework'''

    @property
    def event_manager(self):
        return self._event_manager

    def __init__(self, event_manager):
        super(Publish, self).__init__()
        self._event_manager = event_manager

    def _publish_event(self, event_topic, data, callback):
        '''
        Common method that calls the private publish method from the
        event manager
        '''
        event = ftrack_api.event.base.Event(topic=event_topic, data=data)
        publish_result = self.event_manager._publish(event, callback=callback)
        return publish_result

    def discover_host(self, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.DISCOVER_HOST_TOPIC`
        '''
        topic = constants.DISCOVER_HOST_TOPIC
        return self._publish_event(topic, callback)

    def host_run_definition(self, host_id, definition, engine_type, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.HOST_RUN_DEFINITION_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'definition': definition,
            'engine_type': engine_type,
        }
        event_topic = constants.HOST_RUN_DEFINITION_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_run_plugin(self, host_id, plugin, plugin_type, method, engine_type, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.HOST_RUN_PLUGIN_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'plugin': plugin,
            'plugin_type': plugin_type,
            'method': method,
            'engine_type': engine_type,
        }
        event_topic = constants.HOST_RUN_PLUGIN_TOPIC
        return self._publish_event(event_topic, data, callback)

    def execute_plugin(
            self, plugin_name, plugin_type, method, host_type,
            plugin_data, options, context_data, category='plugin', callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.EXECUTE_PLUGIN_TOPIC`
        '''
        data = {
                'plugin_name': plugin_name,
                'plugin_type': plugin_type,
                'method': method,
                'host_type': host_type,
                'plugin_data': plugin_data,
                'options': options,
                'context_data': context_data,
                'category': category,
            },

        event_topic = constants.EXECUTE_PLUGIN_TOPIC
        return self._publish_event(event_topic, data, callback)

    def discover_plugin(
            self, plugin_name, plugin_type, status, host_type, category='plugin',
            result=None, execution_time=0, message=None, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.DISCOVER_PLUGIN_TOPIC`
        '''
        data = {
                'plugin_name': plugin_name,
                'plugin_type': plugin_type,
                'category': category,
                'host_type': host_type,
                'status': status,
                'result': result,
                'execution_time': execution_time,
                'message': message,
            },

        event_topic = constants.DISCOVER_PLUGIN_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_context_changed(self, host_id, context_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.HOST_CONTEXT_CHANGED_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'context_id': context_id,
        }
        event_topic = constants.HOST_CONTEXT_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_context_changed(self, host_id, context_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.CLIENT_CONTEXT_CHANGED_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'context_id': context_id,
        }
        event_topic = constants.CLIENT_CONTEXT_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_launch_widget(self, host_id, widget_name, source=None, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.CLIENT_LAUNCH_WIDGET_TOPIC`
        '''
        # TODO: call this from a new launch_assembler method in the opener
        #  client or in any other place. The data needed is like the following:
        data = {
            'host_id': host_id,
            'name': widget_name,
            'source': source,
        }

        event_topic = constants.CLIENT_LAUNCH_WIDGET_TOPIC
        return self._publish_event(event_topic, data, callback)

    def notify_client(
            self, host_id, plugin_name, plugin_type, plugin_id=None,
            widget_ref=None, method=None, status=None, result=None,
            execution_time=0, message=None, user_data=None, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.NOTIFY_CLIENT_TOPIC`
        '''
        # TODO: call this from a new launch_assembler method in the opener
        #  client or in any other place. The data needed is like the following:
        data = {
            'host_id': host_id,
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,# Not used
            'plugin_id': plugin_id,
            'widget_ref': widget_ref,
            'method': method, # Not used
            'status': status,
            'result': result,
            'execution_time': execution_time, # Not used
            'message': message,
            'user_data':user_data
        }

        event_topic = constants.NOTIFY_CLIENT_TOPIC
        return self._publish_event(event_topic, data, callback)

    def notify_progress_client(
            self, host_id, step_type, step_name, stage_name,
            total_plugins, current_plugin_index, status,
            results=None, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.NOTIFY_PROGRESS_CLIENT_TOPIC`
        '''
        # TODO: call this from a new launch_assembler method in the opener
        #  client or in any other place. The data needed is like the following:
        data = {
            'host_id': host_id,
            'step_type': step_type,
            'step_name': step_name,# Not used
            'stage_name': stage_name,
            'total_plugins': total_plugins,
            'current_plugin_index': current_plugin_index, # Not used
            'status': status,
            'results': results,
        }

        event_topic = constants.NOTIFY_PROGRESS_CLIENT_TOPIC
        return self._publish_event(event_topic, data, callback)

    def discover_definition(self, host_types, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.DISCOVER_DEFINITION_TOPIC`
        '''
        data = {
            'type': 'definition',
            'host_types': host_types,
        }

        event_topic = constants.DISCOVER_DEFINITION_TOPIC
        return self._publish_event(event_topic, data, callback)


class Subscribe(object):
    '''Class with all the events subscribed by the framework'''
    @property
    def event_manager(self):
        return self._event_manager

    def __init__(self, event_manager):
        super(Subscribe, self).__init__()
        self._event_manager = event_manager

    def _subscribe_event(self, event_topic, callback):
        '''Common method that calls the private subscribe method from the event manager'''
        return self.event_manager._subscribe(event_topic, callback=callback)

    def discover_host(self, callback):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.DISCOVER_HOST_TOPIC`
        '''
        topic = constants.DISCOVER_HOST_TOPIC
        return self._subscribe_event(topic, callback)

    def host_run_definition(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.HOST_RUN_DEFINITION_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.HOST_RUN_DEFINITION_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_run_plugin(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.HOST_RUN_PLUGIN_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.HOST_RUN_PLUGIN_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def execute_plugin(self, host_type, category, plugin_type, plugin_name, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.EXECUTE_PLUGIN_TOPIC`
        '''
        event_topic = (
            '{} and data.host_type={} and data.category={} '
            'and data.plugin_type={} and '
            'data.plugin_name={}'.format(
                constants.EXECUTE_PLUGIN_TOPIC, host_type,
                category, plugin_type, plugin_name
            )
        )
        return self._subscribe_event(event_topic, callback)

    def discover_plugin(self, host_type, category, plugin_type, plugin_name, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.DISCOVER_PLUGIN_TOPIC`
        '''
        event_topic = (
            '{} and data.host_type={} and data.category={} '
            'and data.plugin_type={} and '
            'data.plugin_name={}'.format(
                constants.DISCOVER_PLUGIN_TOPIC, host_type,
                category, plugin_type, plugin_name
            )
        )
        return self._subscribe_event(event_topic, callback)

    def host_context_changed(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.HOST_CONTEXT_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.HOST_CONTEXT_CHANGED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_context_changed(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.CLIENT_CONTEXT_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.CLIENT_CONTEXT_CHANGED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_launch_widget(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.CLIENT_LAUNCH_WIDGET_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.CLIENT_LAUNCH_WIDGET_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def notify_client(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.NOTIFY_CLIENT_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.NOTIFY_CLIENT_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def notify_progress_client(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.NOTIFY_PROGRESS_CLIENT_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.NOTIFY_PROGRESS_CLIENT_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def discover_definition(self, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.DISCOVER_DEFINITION_TOPIC`
        '''
        event_topic = '{} and data.type=definition'.format(
            constants.DISCOVER_DEFINITION_TOPIC
        )
        return self._subscribe_event(event_topic, callback)

