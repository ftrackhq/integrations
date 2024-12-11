# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import logging

logging.basicConfig(level=logging.INFO)


class EventHubThread(threading.Thread):
    """
    Threaded event listener for session's event hub.
    """

    def __init__(self, session):
        _name = id(session)
        super().__init__(name=f"EventHub-{_name}")
        self.session = session
        logging.debug(f"Initializing new EventHubThread for session {session}")
        logging.debug(f"Name set for the thread: {_name}")

    def run(self):
        try:
            logging.info(f"Listening for events on session {self.session}")
            self.session.event_hub.wait()
        except Exception as e:
            logging.error(f"Error in EventHubThread: {e}")
