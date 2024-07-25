# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading

import logging
import ftrack_api
import ftrack_constants.framework as constants
import uuid
import time

from ftrack_utils.event_hub import EventHubThread

logger = logging.getLogger(__name__)


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
        return self._publish_instance

    @property
    def subscribe(self):
        '''
        Property to call the Subscribe class with all the predefined events used
        in the framework
        '''
        return self._subscribe_instance

    def close(self):
        '''Close the event manager and disconnect from the event hub.'''
        self.session.event_hub.disconnect()
        self.session.close()

    def __init__(self, session, mode=constants.event.LOCAL_EVENT_MODE):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_hub_thread = None
        self._mode = mode
        self._session = session
        if mode == constants.event.REMOTE_EVENT_MODE:
            if not self.connected:
                self.logger.error(
                    'Instantiating event manager in Local mode; Session event hub is not connected. Please make sure to connect the event hub before instantiating the EventManager in remote mode. Example: session.event_hub.connect()'
                )
                self._mode = constants.event.LOCAL_EVENT_MODE

        # Initialize Publish and subscribe classes to be able to provide
        # predefined events.
        self._publish_instance = Publish(self)
        self._subscribe_instance = Subscribe(self)

        self.logger.debug(
            f'Initialising event manager {self} with mode {self.mode}'
        )

    def _publish(self, event, callback=None):
        '''Emit *event* and provide *callback* function, in local or remote *remote*.'''

        if self.mode == constants.event.LOCAL_EVENT_MODE:
            result = self.session.event_hub.publish(
                event,
                synchronous=True,
            )

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
        '''Subscribe to ftrack events on the session event hub for *topic* with
        *callback*. Topic should not include the 'topic=' prefix.'''
        subscribe_id = self.session.event_hub.subscribe(
            'topic={}'.format(topic), callback
        )
        return subscribe_id

    def unsubscribe(self, subscribe_id):
        '''Unsubscribe from ftrack events on the session event hub for subscription
        identified by *subscribe_id*. Important to call this on object deletion to
        release dangling callback reference in memory'''
        self.session.event_hub.unsubscribe(subscribe_id)


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
        publish_event = ftrack_api.event.base.Event(
            topic=event_topic, data=data
        )
        publish_result = self.event_manager._publish(
            publish_event, callback=callback
        )
        return publish_result

    def discover_host(self, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_HOST_TOPIC`
        '''
        # TODO: review this implementation, for now this one can't never be remote as it goes into a loop.
        data = None
        event_topic = constants.event.DISCOVER_HOST_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_run_tool_config(
        self, host_id, tool_config_reference, client_options, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_TOOL_CONFIG_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'tool_config_reference': tool_config_reference,
            'client_options': client_options,
        }
        event_topic = constants.event.HOST_RUN_TOOL_CONFIG_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_run_ui_hook(
        self,
        host_id,
        tool_config_reference,
        plugin_config_reference,
        client_options,
        payload,
        callback=None,
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_UI_HOOK_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'tool_config_reference': tool_config_reference,
            'plugin_config_reference': plugin_config_reference,
            'client_options': client_options,
            'payload': payload,
        }
        event_topic = constants.event.HOST_RUN_UI_HOOK_TOPIC
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

    def host_run_ui_hook_result(
        self, host_id, plugin_reference, ui_hook_result, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_UI_HOOK_RESULT_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'plugin_reference': plugin_reference,
            'ui_hook_result': ui_hook_result,
        }

        event_topic = constants.event.HOST_UI_HOOK_RESULT_TOPIC
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

    def client_notify_log_item_added(self, client_id, log_item, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC`
        '''
        data = {
            'client_id': client_id,
            'log_item': log_item,
        }

        event_topic = constants.event.CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_notify_ui_hook_result(
        self, client_id, plugin_reference, ui_hook_result, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_UI_HOOK_RESULT_TOPIC`
        '''
        data = {
            'client_id': client_id,
            'plugin_reference': plugin_reference,
            'ui_hook_result': ui_hook_result,
        }

        event_topic = constants.event.CLIENT_NOTIFY_UI_HOOK_RESULT_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_verify_plugins(self, host_id, plugin_names, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_VERIFY_PLUGINS_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'plugin_names': plugin_names,
        }

        event_topic = constants.event.HOST_VERIFY_PLUGINS_TOPIC
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

    def host_run_tool_config(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_TOOL_CONFIG_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_RUN_TOOL_CONFIG_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_run_ui_hook(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_UI_HOOK_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_RUN_UI_HOOK_TOPIC, host_id
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

    def host_log_item_added(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_LOG_ITEM_ADDED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_LOG_ITEM_ADDED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_run_ui_hook_result(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_LOG_ITEM_ADDED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_UI_HOOK_RESULT_TOPIC, host_id
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

    def client_signal_host_changed(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_notify_log_item_added(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_notify_ui_hook_result(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_UI_HOOK_RESULT_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_NOTIFY_UI_HOOK_RESULT_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_verify_plugins(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_LOG_ITEM_ADDED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_VERIFY_PLUGINS_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)
