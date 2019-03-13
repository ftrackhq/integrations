from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline import event
import logging

logger = logging.getLogger(__name__)


def initalise(session, host, ui):
    event_thread = event.NewApiEventHubThread()
    event_thread.start(session)

    DefintionManager(session)

