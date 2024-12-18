# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ftrack_api import Session

logging.basicConfig(level=logging.INFO)


class EventHubThread(threading.Thread):
    """
    Threaded event listener for session's event hub.
    """

    def __init__(self, session: "Session") -> None:
        _name: int = id(session)
        super().__init__(name=f"EventHub-{_name}")
        self.session: "Session" = session
        logging.debug(f"Initializing new EventHubThread for session {session}")
        logging.debug(f"Name set for the thread: {_name}")

    def run(self) -> None:
        try:
            logging.info(f"Listening for events on session {self.session}")
            self.session.event_hub.wait()
        except Exception:
            logging.error(f"Error in EventHubThread", exc_info=True)
            raise
