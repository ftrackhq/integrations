from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline import event, constants
import logging

logger = logging.getLogger(__name__)


def run(event):
    logger.info('RUNNING: {}'.format(event))


def initalise(session, host, ui):
    event_thread = event.NewApiEventHubThread()
    event_thread.start(session)
    DefintionManager(session)

    session.event_hub.subscribe(
        'topic={}'.format(constants.PIPELINE_RUN_PUBLISHER),
        run
    )



