# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
from collections import OrderedDict
import ftrack_api
from QtExt import QtCore

from ftrack_connect_pipeline import constants


class NewApiEventHubThread(QtCore.QThread):
    '''Listen for events from ftrack's event hub.'''

    def __init__(self, parent=None):
        super(NewApiEventHubThread, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def start(self, session):
        '''Start thread for *_session*.'''
        self._session = session
        self.logger.debug('Starting event hub thread.')
        super(NewApiEventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self.logger.debug('Event hub thread started.')
        self._session.event_hub.wait()


class StageManager(QtCore.QObject):
    '''Manage stages defined in asset definition'''

    # todo: replace with blinker or ftrack-events for abstraction from qt?
    stage_start = QtCore.Signal()
    stage_done = QtCore.Signal()
    stage_error = QtCore.Signal(object)

    stages_end = QtCore.Signal()

    @property
    def widgets(self):
        '''Stores widgets visually representing the stages'''
        return self._widget_stack

    @property
    def results(self):
        '''Stores the final results of each stage.'''
        return self._stages_results

    @property
    def type(self):
        '''Retirm the stage type (publish or load)'''
        return self._stage_type

    @property
    def stages(self):
        '''Stores all the stages definition and callables.'''
        return self._stages_mapping

    @property
    def previous_stage(self):
        '''Return the previous stage.'''
        current_stage_idx = self.stages.keys().index(self.current_stage)

        previous_stage_idx = current_stage_idx - 1

        if previous_stage_idx < 0:
            # we reached the end, no more steps to perform !
            return

        previous_stage = self.stages.keys()[previous_stage_idx]
        return previous_stage

    @property
    def next_stage(self):
        '''Return the next stage.'''
        current_stage_idx = self.stages.keys().index(self.current_stage)

        next_stage_idx = current_stage_idx + 1

        if next_stage_idx >= len(self.stages.keys()):
            self.stages_end.emit()
            # we reached the end, no more steps to perform !
            return

        next_stage = self.stages.keys()[next_stage_idx]
        return next_stage

    @property
    def current_stage(self):
        '''Return the current stage.'''
        return self._current_stage or self.stages.keys()[0]

    @current_stage.setter
    def current_stage(self, stage):
        '''Set the current stage.'''

        if stage not in self.stages.keys():
            self.logger.warning('Stage {} not in {}'.format(stage, self.stages.keys()))
            return

        self._current_stage = stage

    def __init__(self, session, stages_mapping, stage_type):
        '''Initialise with *session*, *stage mapping* and *stage_type*'''
        super(StageManager, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        if not isinstance(stages_mapping, OrderedDict):
            self.logger.error('{} is not an OrderedDict'.format(stages_mapping))

        self._current_stage = None
        self._stages_results = {}
        self._widget_stack = {}

        self._stage_type = stage_type
        self._session = session
        self._stages_mapping = stages_mapping

        self.stage_done.connect(self._on_stage_done)
        self.stage_start.connect(self._on_stage_start)
        self.reset_stages()

    # event handling
    def __on_handle_async_reply(self, event):
        '''handle async ftrack event reply '''
        event_data = event['data']
        event_task_name = event_data.keys()[0]
        event_task_value = event_data.values()[0]

        self.logger.debug(
            'setting result for task: {} as {}'.format(
                event_task_name, event_task_value
            )
        )
        self._stages_results[event_task_name] = event_task_value

        # automatically process next stage
        self.stage_done.emit()

    def run_async(self, event_list):
        '''Run *event_list* asyncronously'''
        self.logger.debug(
            'Sending event list {} to host'.format(event_list)
        )

        self._session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=constants.PIPELINE_RUN_TOPIC,
                data={'event_list': event_list}
            ),
            on_reply=self.__on_handle_async_reply
        )

    def _on_stage_start(self, ):
        '''Slot triggered when the stage start'''
        self.logger.debug('Starting stage: {}'.format(self.current_stage))
        fn = self.stages[self.current_stage][1]
        try:
            fn()
        except Exception as error: # we catch anything as we have no idea what might come from here...
            self.logger.exception(error)
            self.stage_error.emit(str(error))

    def _on_stage_done(self):
        '''Slot triggered when the stage is finished'''
        self.logger.debug('stage: {} done'.format(self.current_stage))
        if not self.next_stage:
            self.reset_stages()
            return

        self.current_stage = self.next_stage
        self.stage_start.emit()

    def process_stages(self):
        '''Process all the stages.'''
        self._reset_results()
        self.stage_start.emit()

    def _reset_results(self):
        '''Reset stages results'''
        for stage in self.stages.keys():
            self.results.setdefault(stage, [])

    def reset_stages(self):
        '''reset stages'''
        self._current_stage = None
