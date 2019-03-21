from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import PublisherRunner
from ftrack_connect_pipeline import event, constants
import logging

logger = logging.getLogger(__name__)


def run(event):
    logger.info('RUNNING: {}'.format(event))


def initalise(session, host, ui):
    event_thread = event.NewApiEventHubThread()
    event_thread.start(session)

    definition_manager = DefintionManager(session)
    PublisherRunner(session, definition_manager.packages, host, ui)




