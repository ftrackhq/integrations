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

    def __init__(self, session, mode=constants.event.LOCAL_EVENT_MODE):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_hub_thread = None
        self._mode = mode
        self._session = session
        if mode == constants.event.REMOTE_EVENT_MODE:
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

        if mode is constants.event.LOCAL_EVENT_MODE:
            result = self.session.event_hub.publish(
                event,
                synchronous=True,
            )

            if result:
                result = result

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
        subscribe_id = self.session.event_hub.subscribe(
            'topic={}'.format(topic), callback
        )
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
        publish_event = ftrack_api.event.base.Event(topic=event_topic, data=data)
        publish_result = self.event_manager._publish(publish_event, callback=callback)
        return publish_result

    def discover_host(self, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_HOST_TOPIC`
        '''

        data = None
        event_topic = constants.event.DISCOVER_HOST_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_run_definition(self, host_id, definition, engine_type, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_DEFINITION_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'definition': definition,
            'engine_type': engine_type,
        }
        event_topic = constants.event.HOST_RUN_DEFINITION_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_run_plugin(
            self, host_id, plugin_definition, plugin_method, engine_type,
            plugin_widget_id=None, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_PLUGIN_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'plugin_definition': plugin_definition,
            'plugin_method': plugin_method,
            'engine_type': engine_type,
            'plugin_widget_id': plugin_widget_id,
        }
        event_topic = constants.event.HOST_RUN_PLUGIN_TOPIC
        return self._publish_event(event_topic, data, callback)

    def execute_plugin(
            self, plugin_name, plugin_default_method, plugin_method, host_type,
            plugin_data, plugin_options, plugin_context_data,
            plugin_widget_id=None, plugin_widget_name=None, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.EXECUTE_PLUGIN_TOPIC`
        '''
        data = {
                'plugin_name': plugin_name,
                'plugin_default_method': plugin_default_method,
                'plugin_method': plugin_method,
                'host_type': host_type,
                'plugin_data': plugin_data,
                'plugin_options': plugin_options,
                'plugin_context_data': plugin_context_data,
                'plugin_widget_id': plugin_widget_id,
                'plugin_widget_name': plugin_widget_name
            }

        event_topic = constants.event.EXECUTE_PLUGIN_TOPIC
        return self._publish_event(event_topic, data, callback)

    def discover_plugin(
            self, host_type, plugin_name, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_PLUGIN_TOPIC`
        '''
        data = {
            'host_type': host_type,
            'plugin_name': plugin_name,
        }

        event_topic = constants.event.DISCOVER_PLUGIN_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_context_changed(self, host_id, context_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_CONTEXT_CHANGED_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'context_id': context_id,
        }
        event_topic = constants.event.HOST_CONTEXT_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_context_changed(self, host_id, context_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_CONTEXT_CHANGED_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'context_id': context_id,
        }
        event_topic = constants.event.CLIENT_CONTEXT_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_launch_widget(self, host_id, widget_name, source=None, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_LAUNCH_WIDGET_TOPIC`
        '''
        # TODO: call this from a new launch_assembler method in the opener
        #  client or in any other place. The data needed is like the following:
        data = {
            'host_id': host_id,
            'name': widget_name,
            'source': source,
        }

        event_topic = constants.event.CLIENT_LAUNCH_WIDGET_TOPIC
        return self._publish_event(event_topic, data, callback)

    def notify_plugin_progress_client(
            self, plugin_info, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.NOTIFY_PLUGIN_PROGRESS_TOPIC`
        '''
        event_topic = constants.event.NOTIFY_PLUGIN_PROGRESS_TOPIC
        return self._publish_event(event_topic, plugin_info, callback)

    def notify_definition_progress_client(
            self, host_id, step_type, step_name, stage_name,
            total_plugins, current_plugin_index, status,
            results=None, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.NOTIFY_DEFINITION_PROGRESS_CLIENT_TOPIC`
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

        event_topic = constants.event.NOTIFY_DEFINITION_PROGRESS_CLIENT_TOPIC
        return self._publish_event(event_topic, data, callback)

    def discover_definition(self, host_types, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_DEFINITION_TOPIC`
        '''
        data = {
            'type': 'definition',
            'host_types': host_types,
        }

        event_topic = constants.event.DISCOVER_DEFINITION_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_log_item_added(self, host_id, log_item, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_LOG_ITEM_ADDED_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'log_item': log_item,
        }

        event_topic = constants.event.HOST_LOG_ITEM_ADDED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_signal_context_changed(self, client_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC`
        '''
        data = {
            'client_id': client_id,
        }

        event_topic = constants.event.CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_signal_hosts_discovered(self, client_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC`
        '''
        data = {
            'client_id': client_id,
        }

        event_topic = constants.event.CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_signal_host_changed(self, client_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC`
        '''
        data = {
            'client_id': client_id,
        }

        event_topic = constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_signal_definition_changed(self, client_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_DEFINITION_CHANGED_TOPIC`
        '''
        data = {
            'client_id': client_id,
        }

        event_topic = constants.event.CLIENT_SIGNAL_DEFINITION_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_notify_ui_run_plugin_result(self, client_id, plugin_info, callback=None):
        data = {
            'client_id': client_id,
            'plugin_info': plugin_info,
        }

        event_topic = constants.event.CLIENT_NOTIFY_UI_RUN_PLUGIN_RESULT_TOPIC
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
        :const:`~ftrack_framework_core.constants.event.DISCOVER_HOST_TOPIC`
        '''
        topic = constants.event.DISCOVER_HOST_TOPIC
        return self._subscribe_event(topic, callback)

    def host_run_definition(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_DEFINITION_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_RUN_DEFINITION_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_run_plugin(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_PLUGIN_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_RUN_PLUGIN_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def execute_plugin(self, host_type, plugin_name, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.EXECUTE_PLUGIN_TOPIC`
        '''
        event_topic = (
            '{} and data.host_type={}'
            ' and data.plugin_name={}'.format(
                constants.event.EXECUTE_PLUGIN_TOPIC, host_type, plugin_name
            )
        )
        return self._subscribe_event(event_topic, callback)

    def discover_plugin(self, host_type, plugin_name, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_PLUGIN_TOPIC`
        '''
        event_topic = (
            '{} and data.host_type={}'
            ' and data.plugin_name={}'.format(
                constants.event.DISCOVER_PLUGIN_TOPIC, host_type, plugin_name
            )
        )
        return self._subscribe_event(event_topic, callback)

    def host_context_changed(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_CONTEXT_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_CONTEXT_CHANGED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_context_changed(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_CONTEXT_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.CLIENT_CONTEXT_CHANGED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_launch_widget(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_LAUNCH_WIDGET_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.CLIENT_LAUNCH_WIDGET_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def notify_plugin_progress_client(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.NOTIFY_PLUGIN_PROGRESS_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.NOTIFY_PLUGIN_PROGRESS_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def notify_definition_progress_client(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.NOTIFY_DEFINITION_PROGRESS_CLIENT_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.NOTIFY_DEFINITION_PROGRESS_CLIENT_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def discover_definition(self, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_DEFINITION_TOPIC`
        '''
        event_topic = '{} and data.type=definition'.format(
            constants.event.DISCOVER_DEFINITION_TOPIC
        )
        return self._subscribe_event(event_topic, callback)

    def host_log_item_added(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_LOG_ITEM_ADDED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_LOG_ITEM_ADDED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_signal_context_changed(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_signal_hosts_discovered(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_signal_host_changed(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_signal_definition_changed(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_DEFINITION_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_SIGNAL_DEFINITION_CHANGED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_notify_ui_run_plugin_result(self, client_id, callback=None):
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_NOTIFY_UI_RUN_PLUGIN_RESULT_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)
