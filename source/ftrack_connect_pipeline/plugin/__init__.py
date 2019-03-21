# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import exception


class _Base(object):

    plugin_type = None
    plugin_name = None
    type = None
    host = constants.HOST
    ui = constants.UI
    return_type = None

    @property
    def topic(self):
        return NotImplementedError()

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session):
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._session = session

    def register(self):
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        self.logger.debug('registering: {} for {}'.format(
            self.plugin_name, self.plugin_type)
        )

        self.session.event_hub.subscribe(
            self.topic, self._run
        )

    def run(self, context=None, data=None, options=None):
        raise NotImplementedError('Missing run method.')

    def _run(self, event):
        settings = event['data']['settings']
        self.logger.debug(settings)
        result = self.run(**settings)

        if self.return_type:
            if not isinstance(result , self.return_type):
                raise Exception(
                    'Return value of {} is of type {}, should return {} type'.format(
                        self, type(result), self.return_type
                    )
                )

        return result


class BasePlugin(_Base):
    type = 'plugin'

    @property
    def topic(self):
        required = [
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name,
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = (
            'topic={} and '
            'data.pipeline.host={} and '
            'data.pipeline.type={} and '
            'data.pipeline.plugin_type={} and '
            'data.pipeline.plugin_name={}'
        ).format(
            constants.PIPELINE_REGISTER_PLUGIN_TOPIC,
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name
        )
        return topic


class BaseWidget(_Base):
    type = 'widget'

    @property
    def topic(self):
        required = [
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name,
            self.ui
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = (
            'topic={} and '
            'data.pipeline.host={} and '
            'data.pipeline.ui={} and '
            'data.pipeline.type={} and '
            'data.pipeline.plugin_type={} and '
            'data.pipeline.plugin_name={}'
        ).format(
            constants.PIPELINE_REGISTER_PLUGIN_TOPIC,
            self.host,
            self.ui,
            self.type,
            self.plugin_type,
            self.plugin_name
        )
        return topic


class ContextPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.CONTEXT


class ContextWidget(BaseWidget):
    plugin_type = constants.CONTEXT


from ftrack_connect_pipeline.plugin.load import *
from ftrack_connect_pipeline.plugin.publish import *