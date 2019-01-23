import ftrack_api
import logging
from ftrack_connect_pipeline import constants
from QtExt import QtCore


class NewApiEventHubThread(QtCore.QThread):
    '''Listen for events from ftrack's event hub.'''

    def start(self, session):
        '''Start thread for *_session*.'''
        self._session = session
        super(NewApiEventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self._session.event_hub.wait()


class StageManager(QtCore.QObject):

    # todo: replace with blinker or ftrack-events for abstraction from qt?
    stage_start = QtCore.Signal()
    stage_done = QtCore.Signal()

    @property
    def widgets(self):
        return self._widget_stack

    @property
    def results(self):
        return self._stages_results

    @property
    def type(self):
        return self._stage_type

    @property
    def stages(self):
        return self._stages_mapping

    @property
    def previous_stage(self):
        self.logger.info('current_stage :{}'.format(self.current_stage))
        current_stage_idx = self.stages.keys().index(self.current_stage)

        previous_stage_idx = current_stage_idx - 1

        if previous_stage_idx < 0:
            # we reached the end, no more steps to perform !
            return

        previous_stage = self.stages.keys()[previous_stage_idx]
        self.logger.info('previous_stage :{}'.format(previous_stage))
        return previous_stage

    @property
    def next_stage(self):
        self.logger.info('current_stage :{}'.format(self.current_stage))
        current_stage_idx = self.stages.keys().index(self.current_stage)

        next_stage_idx = current_stage_idx + 1

        if next_stage_idx >= len(self.stages.keys()):
            # we reached the end, no more steps to perform !
            return

        next_stage = self.stages.keys()[next_stage_idx]
        self.logger.info('next_stage :{}'.format(next_stage))
        return next_stage

    @property
    def current_stage(self):
        return self._current_stage or self.stages.keys()[0]

    @current_stage.setter
    def current_stage(self, stage):
        if stage not in self.stages.keys():
            self.logger.warning('Stage {} not in {}'.format(stage, self.stages.keys()))
            return

        self._current_stage = stage

    def __init__(self, session, stages_mapping, stage_type):
        super(StageManager, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._current_stage = None
        self._stage_type = stage_type
        self._stages_results = {}
        self._session = session
        self._stages_mapping = stages_mapping
        self._widget_stack = {}

        self.stage_done.connect(self._on_stage_done)
        self.stage_start.connect(self._on_stage_start)

    # event handling
    def _on_handle_async_reply(self, event):
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
        self.logger.debug(
            'Sending event list {} to host'.format(event_list)
        )

        self._session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic=constants.PIPELINE_RUN_TOPIC,
                data={'event_list': event_list}
            ),
            on_reply=self._on_handle_async_reply
        )

    def _on_stage_start(self, ):
        self.logger.debug('Starting stage: {}'.format(self.current_stage))
        fn = self.stages[self.current_stage][1]
        fn()

    def _on_stage_done(self):
        self.logger.debug('stage: {} done'.format(self.current_stage))
        if not self.next_stage:
            self.reset_stages()
            return

        self.current_stage = self.next_stage
        self.stage_start.emit()

    def process_stages(self):
        self._reset_results()
        self.stage_start.emit()

    def _reset_results(self):
        for stage in self.stages.keys():
            self.results.setdefault(stage, [])

    def reset_stages(self):
        self._current_stage = None
