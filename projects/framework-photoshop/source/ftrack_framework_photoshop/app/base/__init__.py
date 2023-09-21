# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import traceback
import sys
import subprocess
import re
import time
import os
import atexit
import signal

from Qt import QtWidgets, QtCore

import ftrack_api

from ftrack_constants import framework as constants
from ftrack_framework_photoshop import constants as photoshop_constants
from ftrack_qt import event as qt_event
from ftrack_framework_core import host
from ftrack_framework_core import event as event
from ftrack_framework_core import client


logger = logging.getLogger(__name__)


class BasePhotoshopApplication(QtWidgets.QApplication):
    ''' Base Photoshop standalone background application.'''

    _instance = None

    @property
    def integration_session_id(self):
        return self._integration_session_id

    @property
    def photoshop_version(self):
        return self._photoshop_version

    @property
    def event_manager(self):
        return self._event_manager

    @property
    def session(self):
        return self.event_manager.session

    @property
    def remote_event_manager(self):
        return self._remote_event_manager

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        self._connected = value
        if self.connect:
            logger.info(
                'Successfully established connection to Photoshop {}'.format(
                    self.photoshop_version
                )
            )

            self._photoshop_pid = self._probe_photoshop_pid()

            assert (
                self._photoshop_pid > 0
            ), "Could not find Photoshop PID among running processes!"

    def __init__(self, integration_session_id, photoshop_version):
        super(BasePhotoshopApplication, self).__init__()

        self._integration_session_id = integration_session_id
        self._photoshop_version = photoshop_version
        self._event_manager = None
        self._remote_event_manager = None
        self._photoshop_pid = -1
        self._connected = False

        BasePhotoshopApplication._instance = self

        try:
            self._initialise()
        except:
            logger.warning(traceback.format_exc())
            self.terminate()

    # PID

    def _probe_photoshop_pid(self):
        ''' List processes using 'ps' to find photoshop pid '''
        PS_EXECUTABLE = "Adobe Photoshop {}".format(
            str(self._photoshop_version)
        )

        logger.info(
            'Probing PID (executable: {}).'.format(
                PS_EXECUTABLE
            )
        )

        if sys.platform == 'darwin':
            for line in subprocess.check_output(["ps", "-ef"]).decode('utf-8').split("\n"):
                if line.find('MacOS/{}'.format(PS_EXECUTABLE)) > -1:
                    # Expect:
                    #   501 21270     1   0  3:05PM ??         0:36.85 /Applications/Adobe Photoshop 2022/Adobe Photoshop 2022.app/Contents/MacOS/Adobe Photoshop 2022
                    pid = int(re.split(" +", line)[2])
                    logger.info(
                        'Got Photoshop PID: {}'.format(
                            pid
                        )
                    )
                    return pid
        logger.warning(
            'Photoshop not found running!'
        )
        return -1

    # Event

    def handle_remote_event(self, event):
        eid = event['id']
        topic = event['topic']
        event_data = event['data']
        source = event.get('source')
        logger.info(
            'Processing incoming PS event: {} ({}), data: {}, source: {}'.format(
                topic, eid, event_data, source
            )
        )

        if topic == photoshop_constants.TOPIC_PING:
            self.connected = True
            # Send pong back with current context data
            context_id = os.getenv('FTRACK_CONTEXTID')
            task = self.session.query(
                'Task where id={}'.format(context_id)
            ).one()
            self.send_event(
                photoshop_constants.TOPIC_PONG,
                {
                    'context_id': context_id,
                    'context_name': task['name'],
                    'context_type': task['type']['name'],
                    'context_path': " / ".join(
                        [d["name"] for d in task["link"][:-1]]
                    ),
                    'context_thumbnail': task['thumbnail_url']['url'],
                    'project_id': task['project_id'],
                },
            )

    def send_event(
        self, topic, pipeline_data, fetch_reply=False, timeout=None
    ):
        if pipeline_data is None:
            pipeline_data = dict()
        if timeout is None:
            timeout = 10
        pipeline_data['integration_session_id'] = self.integration_session_id

        event = ftrack_api.event.base.Event(
            topic=topic, data={'pipeline': pipeline_data}
        )

        logger.info(
            "Sending PS event: {} (fetch_reply: {})".format(event, fetch_reply)
        )

        subscriber_id = None
        self._replies[event['id']] = None

        def handle_reply(reply_event):
            logger.info("Handle reply: {}".format(reply_event))

            self._replies[event['id']] = reply_event

        if fetch_reply:
            # Temp subscribe for response
            subscriber_id = self.remote_event_manager.subscribe(
                'ftrack.* and source.applicationId=ftrack.api.javascript and data.pipeline.integration_session_id={} '
                'and data.pipeline.reply_to_event={}'.format(
                    self.integration_session_id, event['id']
                ),
                handle_reply,
            )
        try:
            self.remote_event_manager.publish(event)
            if fetch_reply:
                # Wait for response, block
                waited = 0
                if timeout is None:
                    timeout = 10
                while self._replies[event['id']] is None:
                    time.sleep(0.1)
                    waited += 100
                    if waited > timeout * 1000:
                        raise Exception(
                            'Timeout waiting for reply to event: {}'.format(
                                event['id']
                            )
                        )
                    if waited % 1000 == 0:
                        logger.info(
                            'Waited {}s for reply to event: {}'.format(
                                waited / 1000, event['id']
                            )
                        )
                return self._replies[event['id']]['data']['pipeline']
        finally:
            if subscriber_id:
                self.remote_event_manager.unsubscribe(subscriber_id)
            if event['id'] in self._replies:
                del self._replies[event['id']]

    def send_event_with_reply(self, topic, pipeline_data, timeout=None):
        return self.send_event(
            topic, pipeline_data, fetch_reply=True, timeout=timeout
        )


    # Lifecycle

    def _initialise(self):
        ''' Initialise Photoshop standalone integration'''

        logger.info(
            'Setting up photoshop standalone integration (session id: {})...'.format(
                self.integration_session_id
            )
        )

        session = ftrack_api.Session(auto_connect_event_hub=False)

        self._event_manager = qt_event.QEventManager(
            session=session, mode=constants.event.LOCAL_EVENT_MODE
        )

        self._host = host.Host(self.event_manager)

        self._client = client.Client(self.event_manager)

        # TODO: Define tools here

        # Establish connection to Photoshop, will throw exception if failed
        self._connect()

        # Wait for Photoshop to get ready to receive events
        time.sleep(0.5)

        def on_exit():
            logger.info('Photoshop pipeline exit')

        atexit.register(on_exit)

    def _connect(self):
        ''' Connect with DCC over remote event hub, needs to be implemented by
         Photoshop plugin dependent subclass implementation '''
        raise NotImplemented()


    def _spawn_event_listener(self):
        # Create a session and Event Manager

        remote_session = ftrack_api.Session(auto_connect_event_hub=True)

        self._remote_event_manager = event.EventManager(
            session=remote_session, mode=constants.event.REMOTE_EVENT_MODE
        )

        logger.info(
            'Registering remote event listener (photoshop session id: {})'.format(
                self.integration_session_id
            )
        )

        self.remote_event_manager.subscribe(
            'ftrack.pipeline.* and source.applicationId=ftrack.api.javascript and data.pipeline.integration_session_id={}'.format(
                self.integration_session_id
            ),
            self.handle_remote_event,
        )

        # print('@@@ Debug threads:')
        # for threadId, stack in list(sys._current_frames().items()):
        #    print('@@@  Thread ID: {}'.format(threadId))
        #    for filename, lineno, name, line in traceback.extract_stack(stack):
        #        print('@@@   File: "%s", line %d, in %s' % (filename, lineno, name))

        # DEBUG
        def handle_event_debug(event):
            logger.warning("DEBUG event: {}".format(event))

        self.remote_event_manager.subscribe(
            'ftrack.*',
            handle_event_debug,
        )


    def check_responding(self):
        '''Check if Photoshop is alive, send ping'''
        logger.info("Checking if PS is still alive...")
        try:
            self.send_event_with_reply(photoshop_constants.TOPIC_PING, {})
        except:
            logger.warning(traceback.format_exc())
            return False
        return True

    def check_alive(self):
        '''Check if PID is running'''
        logger.info(
            "Checking if PS is still alive (pid: {})...".format(
                self._photoshop_pid
            )
        )

        pid = self._probe_photoshop_pid()
        return pid == self._photoshop_pid

    def terminate(self):
        logger.info("Terminating Photoshop standalone framework integration")
        os.kill(os.getpid(), signal.SIGKILL)
