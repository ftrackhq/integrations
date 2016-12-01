# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline.ui.publish import workflow_selector
import ftrack_connect_pipeline.ui.widget.header
from ftrack_connect_pipeline.ui.widget.context_selector import ContextSelector
import ftrack_connect_pipeline.ui.publish.workflow
import ftrack_connect_pipeline.util


class Dialog(QtWidgets.QDialog):
    '''Publish dialog that lists workflows and content.'''

    def __init__(self, session):
        '''Instantiate with *session*.'''
        self.session = session
        super(Dialog, self).__init__()

        self.current_workflow = None

        self.setLayout(QtWidgets.QVBoxLayout())

        entity = ftrack_connect_pipeline.util.get_ftrack_entity()
        self.context_selector = ContextSelector(entity)
        self.context_selector.entityChanged.connect(self.on_context_changed)

        self.layout().addWidget(
            ftrack_connect_pipeline.ui.widget.header.Header(session)
        )
        self.layout().addWidget(self.context_selector)

        self.publish_container = QtWidgets.QWidget()
        self.publish_container.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.publish_container)

        selector_widget = workflow_selector.WorkflowSelector(
            self.session
        )
        selector_widget._allSection.actionLaunched.connect(
            self._handle_actions_launched
        )
        self.publish_container.layout().addWidget(selector_widget)

    def on_context_changed(self, entity):
        '''Set the current context to the given *entity*.'''
        # :TODO: Fix this and connect to the real entity.
        self.publish_asset.switch_entity(entity)

    def _handle_actions_launched(self, action, results):
        if len(results) != 1:
            raise ValueError(
                'Only one action allowed, got: {0!r}.'.format(results)
            )

        result = results.pop()
        workflow = result['workflow']
        print workflow

        ftrack_connect_pipeline.util.invoke_in_main_thread(
            self.set_active_workflow,
            workflow
        )

    def set_active_workflow(self, workflow):
        new_workflow = (
            ftrack_connect_pipeline.ui.publish.workflow.Workflow(
                **workflow
            )
        )

        if self.current_workflow is not None:
            self.publish_container.layout().removeWidget(self.current_workflow)
            self.current_workflow.setParent(None)

        self.publish_container.layout().addWidget(new_workflow)

        self.current_workflow = new_workflow
