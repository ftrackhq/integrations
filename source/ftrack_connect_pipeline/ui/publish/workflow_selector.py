# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import ftrack_connect_pipeline.ui.widget.actions
from ftrack_connect_pipeline.config import configure_logging


class WorkflowSelector(ftrack_connect_pipeline.ui.widget.actions.Actions):
    '''Publish actions dialog.

    As of not this class is kind of hacky to tweak behaviours in the base
    class that should be easier to configure, perhaps even separated.

    '''

    def __init__(self, session, **kwargs):
        '''Instantiate publish actions dialog.'''
        super(WorkflowSelector, self).__init__(
            session,
            **kwargs
        )
        configure_logging('ftrack_connect_pipeline')
        self.setObjectName('ftrack-workflow-selector')
        layout = self.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        item = layout.itemAt(0)
        item.widget().hide()
        self._recentLabel.hide()
        self._recentSection.hide()

    def _updateRecentSection(self, *args, **kwargs):
        '''Override and supress update of recent section.'''
        pass
