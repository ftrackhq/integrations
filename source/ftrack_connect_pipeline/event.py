# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import threading

import functools
import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.session import get_shared_session

logger = logging.getLogger(__name__)

from QtExt import QtCore


class _EventThread(threading.Thread):
    '''Wrapper object to simulate asyncronus events.'''
    def __init__(self, session, event, callback=None):
        super(_EventThread, self).__init__(target=self.run)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._callback = callback
        self._event = event
        self._session = session
        self._result = {}

    def run(self):
        '''Target thread method.'''
        result = self._session.event_hub.publish(
            self._event,
            synchronous=True,
        )

        # Mock async event reply.
        event = ftrack_api.event.base.Event(
            topic=u'ftrack.meta.reply',
            data=result,
            in_reply_to_event=self._event['id'],
        )

        if self._callback:
            self._callback(event)


class EventManager(object):
    '''Manages the events handling.'''
    def __init__(self, session):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = session

    def publish(self, event, callback=None, remote=False):
        '''Emit *event* and provide *callback* function.'''

        if not remote:
            self.logger.info('running local events')
            event_thread = _EventThread(self.session, event, callback)
            event_thread.start()

        else:
            self.logger.info('running remote events')
            self.session.event_hub.publish(
                event,
                on_reply=callback
            )


class NewApiEventHubThread(QtCore.QThread):
    '''Listen for events from ftrack's event hub.'''

    def __init__(self, parent=None):
        super(NewApiEventHubThread, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def start(self, session):
        '''Start thread for *_session*.'''
        self._session = session
        self.logger.debug('Starting event hub thread.')
        super(NewApiEventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self.logger.debug('Event hub thread started.')
        self._session.event_hub.wait()

#
# def _run_local_events(session, event, host=None, ui=None):
#     logger.info('run_local_events:{}'.format(event))
#     event_list = event['data']['event_list']
#     results = []
#     event_type = None
#     for one_event in event_list:
#         event_type = one_event['pipeline']['plugin_type']
#
#         logger.info('one event: {}'.format(one_event))
#
#         event = ftrack_api.event.base.Event(
#             topic=constants.PIPELINE_REGISTER_TOPIC,
#             data=one_event
#         )
#         result = session.event_hub.publish(
#             event,
#             synchronous=True
#         )
#
#         if result:
#             results.append(result[0])
#
#     local_event_result = {event_type: results}
#     logger.info('one event result: {}'.format(local_event_result))
#     return local_event_result
#
#
# def start_host_listener(host=None, ui=None):
#     logger.info('start event listener')
#     session = get_shared_session()
#     session.event_hub.subscribe(
#         'topic={}'.format(constants.PIPELINE_RUN_PUBLISHER),
#         functools.partial(_run_local_events, session, host=host, ui=ui)
#     )
#     session.event_hub.wait()
