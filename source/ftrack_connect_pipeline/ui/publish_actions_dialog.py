# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtWidgets

import ftrack_connect_pipeline.ui.widget.actions
import ftrack_connect_pipeline.ui.widget.header
from ftrack_connect_pipeline.config import configure_logging


class PublishActionsDialog(ftrack_connect_pipeline.ui.widget.actions.Actions):
    '''Publish actions dialog.

    As of not this class is kind of hacky to tweak behaviours in the base
    class that should be easier to configure, perhaps even separated.

    '''

    def __init__(self, session, **kwargs):
        '''Instantiate publish actions dialog.'''
        super(PublishActionsDialog, self).__init__(session, **kwargs)
        configure_logging('ftrack_connect_pipeline')
        layout = self.layout()
        item = layout.itemAt(0)
        item.widget().hide()
        self._recentLabel.hide()
        self._recentSection.hide()
        header = ftrack_connect_pipeline.ui.widget.header.Header(session)
        layout.insertWidget(0, header)

    def _updateRecentSection(self, *args, **kwargs):
        '''Override and supress update of recent section.'''
        pass


def show(session):
    '''Show actions list dialog.'''
    dialog = QtWidgets.QDialog()
    layout = QtWidgets.QVBoxLayout()
    dialog.setLayout(layout)
    layout.addWidget(
        PublishActionsDialog(
            session, all_section_text='<h3>What do you want to publish?</h3>'
        )
    )
    dialog.setMinimumSize(600, 400)
    dialog.exec_()
