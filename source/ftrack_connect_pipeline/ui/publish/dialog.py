# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from Qt import QtWidgets, QtCore

import ftrack_connect_pipeline.ui.widget.overlay
from ftrack_connect_pipeline.ui.publish import workflow_selector
import ftrack_connect_pipeline.ui.widget.header
from ftrack_connect_pipeline.ui.widget.context_selector import ContextSelector
import ftrack_connect_pipeline.ui.publish.workflow
import ftrack_connect_pipeline.util
from ftrack_connect_pipeline.ui import theme 


class Dialog(QtWidgets.QDialog):
    '''Publish dialog that lists workflows and content.'''

    def __init__(self, ftrack_entity, session):
        '''Instantiate with *session*.'''
        self.session = session
        super(Dialog, self).__init__()
        theme.applyTheme(self, theme='dark')
        theme.applyFont()
        self.setLayout(QtWidgets.QVBoxLayout())

        self.active_workflow_widget = None

        self.context_selector = ContextSelector(ftrack_entity)
        self.context_selector.entityChanged.connect(self.on_context_changed)

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

        self.placeholder_widget = QtWidgets.QLabel(
            '<center><h3>Select what to publish</h3></center>'
        )

        self.publish_container.layout().addWidget(selector_widget)
        self.publish_container.layout().addWidget(
            self.placeholder_widget,
            stretch=1
        )

    def on_context_changed(self, ftrack_entity):
        '''Set the current context to the given *ftrack_entity*.'''
        ftrack_connect_pipeline.util.set_ftrack_entity(ftrack_entity['id'])
        if self.active_workflow_widget:
            self.remove_active_workflow_widget()
            self.publish_container.layout().addWidget(
                self.placeholder_widget,
                stretch=1
            )

    def remove_active_workflow_widget(self):
        '''Remove active workflow widget from container.'''
        self.publish_container.layout().removeWidget(
            self.active_workflow_widget
        )
        self.active_workflow_widget.setParent(None)
        self.active_workflow_widget = None

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
            action['label'], publish_asset
        )

    def set_active_workflow(self, label, publish_asset):
        '''Set the active *workflow*.'''
        if self.active_workflow_widget:
            self.remove_active_workflow_widget()
        else:
            self.publish_container.layout().removeWidget(
                self.placeholder_widget
            )

        self.active_workflow_widget = (
            ftrack_connect_pipeline.ui.publish.workflow.Workflow(
                label=label,
                description=publish_asset.description,
                publish_asset=publish_asset,
                session=self.session
            )
        )
        self.publish_container.layout().addWidget(self.active_workflow_widget)
