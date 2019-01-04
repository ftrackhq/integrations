import logging

import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.configure_logging import configure_logging
import copy

configure_logging(__name__)
logger = logging.getLogger(__name__)


registry = {}


def register_assets(session):
    results = session.event_hub.publish(
        ftrack_api.event.base.Event(
            topic=constants.REGISTER_ASSET_TOPIC,
            data=dict()
        ),
        synchronous=True
    )
    for result in results[0]:
        registry[result['asset_name']] = result

    return registry


def get_registered_assets(entity_type):
    filtered_results = {}
    for asset_name , asset_data in registry.items():
        if entity_type in asset_data['context']:
            filtered_results[asset_name] = asset_data

    return copy.deepcopy(filtered_results)
