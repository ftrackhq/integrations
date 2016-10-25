import ftrack_connect_pipeline.ui.widget.actions

from QtExt import QtGui, QtCore, QtWidgets


class PublishActionsDialog(ftrack_connect_pipeline.ui.widget.actions.Actions):
    '''Publish actions dialog.

    As of not this class is kind of hacky to tweak behaviours in the base
    class that should be easier to configure, perhaps even separated.

    '''

    def __init__(self, *args, **kwargs):
        '''Instantiate publish actions dialog.'''
        super(PublishActionsDialog, self).__init__(*args, **kwargs)

        layout = self.layout()
        item = layout.itemAt(0)
        item.widget().hide()
        self._recentLabel.hide()
        self._recentSection.hide()

    def _updateRecentSection(self, *args, **kwargs):
        '''Override and supress update of recent section.'''
        pass


def show(session):
    '''Show actions list dialog.'''
    dialog = QtWidgets.QDialog()
    layout = QtWidgets.QVBoxLayout()
    dialog.setLayout(layout)
    layout.addWidget(PublishActionsDialog(session))
    dialog.setMinimumSize(600, 400)
    dialog.exec_()
