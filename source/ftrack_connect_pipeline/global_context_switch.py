# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack


from QtExt import QtWidgets
from QtExt import QtCore

from ftrack_connect_pipeline.ui.widget import context_selector


class GlobalSwitchDialog(QtWidgets.QDialog):
    '''Global context switch tool.'''

    # Emitted when context changes.
    context_changed = QtCore.Signal(object)

    def __init__(self, current_entity):
        '''Initialize GlobalSwitchDialog with *current_entity*.'''
        super(GlobalSwitchDialog, self).__init__()
        self.setWindowTitle('Global Context Switch')
        layout = QtWidgets.QVBoxLayout()
        self._session = current_entity.session
        self.setLayout(layout)
        self._entity_browser = context_selector.EntityBrowser()
        layout.addWidget(self._entity_browser)
        current_location = [e['id'] for e in current_entity['link']]
        self._entity_browser.setLocation(current_location)
        self._entity_browser.accepted.connect(self.on_context_changed)
        self._entity_browser.rejected.connect(self.close)
        self.context_changed.connect(self.on_notify_user)

    def on_context_changed(self):
        '''Handle context change event.'''
        selected_entity = self._entity_browser.selected()[0]
        self.close()
        self.context_changed.emit(selected_entity['id'])

    def on_notify_user(self, context_id):
        '''Handle user notification on context change event.'''
        context = self._session.get('Context', context_id)
        parents = ' / '.join([c['name'] for c in context['link']])

        QtWidgets.QMessageBox.information(
            self,
            'Context Changed',
            u'You have now changed context to: {0}'.format(parents)
        )


class GlobalContextSwitch(object):
    '''Global context switch.'''

    def __init__(self, plugin):
        '''Initialise with *plugin*.'''
        self.plugin = plugin

    def open(self):
        '''Create and open the global context switch.'''
        dialog = GlobalSwitchDialog(
            self.plugin.get_context()
        )
        dialog.context_changed.connect(self.plugin.set_context)
        dialog.exec_()
