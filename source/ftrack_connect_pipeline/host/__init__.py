from ftrack_connect_pipeline.host.definition import DefintionManager
import logging

logger = logging.getLogger(__name__)


def initalise(session, host, ui):
    DefintionManager(session)

