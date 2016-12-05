# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from Qt import QtWidgets

import ftrack_connect_pipeline.ui.widget.overlay
from ftrack_connect_pipeline.ui.publish import workflow_selector
import ftrack_connect_pipeline.ui.widget.header
from ftrack_connect_pipeline.ui.widget.context_selector import ContextSelector
import ftrack_connect_pipeline.ui.publish.workflow
import ftrack_connect_pipeline.util


class Dialog(QtWidgets.QDialog):
    '''Publish dialog that lists workflows and content.'''

    def __init__(self, session, entity):
        '''Instantiate with *session*.'''
        self.session = session
        super(Dialog, self).__init__()

        self.active_workflow = None

        self.setLayout(QtWidgets.QVBoxLayout())

        self.context_selector = ContextSelector(entity)

        self.layout().addWidget(
            ftrack_connect_pipeline.ui.widget.header.Header(session)
        )
        self.layout().addWidget(self.context_selector)

        self.publish_container = QtWidgets.QWidget()
        self.publish_container.setLayout(QtWidgets.QHBoxLayout())
        self.publish_container.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.publish_container)

        overlay_widget = ftrack_connect_pipeline.ui.widget.overlay.BusyOverlay(
            self, message='Preparing publish...'
        )

        selector_widget = workflow_selector.WorkflowSelector(
            self.session, overlay=overlay_widget
        )
        selector_widget.setFixedWidth(100)
        selector_widget._allSection.actionLaunched.connect(
            self._handle_actions_launched
        )
        self.publish_container.layout().addWidget(selector_widget)
        self.publish_container.layout().addWidget(
            QtWidgets.QLabel(
                '<center><h3>Select what to publish</h3></center>'
            ),
            stretch=1
        )

    def _handle_actions_launched(self, action, results):
        '''Handle launch of action *action* and *results*.'''
        if len(results) != 1:
            raise ValueError(
                'Only one action allowed, got: {0!r}.'.format(results)
            )

        result = results.pop()
        publish_asset = result['publish_asset']
        ftrack_connect_pipeline.util.invoke_in_main_thread(
            self.set_active_workflow,
            action['label'],
            publish_asset
        )

    def set_active_workflow(self, label, publish_asset):
        '''Set the active *publish_asset*.'''
        publish_widget = self.publish_container.layout().itemAt(1).widget()
        self.publish_container.layout().removeWidget(publish_widget)
        publish_widget.setParent(None)

        self.active_workflow = (
            ftrack_connect_pipeline.ui.publish.workflow.Workflow(
                label=label,
                publish_asset=publish_asset,
                context_selector=self.context_selector,
                session=self.session
            )
        )

        self.publish_container.layout().addWidget(self.active_workflow)
