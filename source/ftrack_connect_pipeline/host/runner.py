from ftrack_connect_pipeline import constants


class PublisherRunner(object):
    def __init__(self, session):
        self.session = session

        session.event_hub.subscribe(
            'topic={}'.format(constants.PIPELINE_RUN_PUBLISHER),
            run
        )

