# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack


from QtExt import QtWidgets
from QtExt import QtCore

from ftrack_connect_pipeline import util
from ftrack_connect_pipeline.ui.widget import context_selector


class GlobalSwitch(QtWidgets.QDialog):
    '''Global Context Switch'''
    context_changed = QtCore.Signal(object)

    def __init__(self, current_entity):
        super(GlobalSwitch, self).__init__()
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
        entity_id = selected_entity['id']
        util.set_ftrack_entity(entity_id)
        self.close()
        self.context_changed.emit(entity_id)

    def on_notify_user(self, context_id):
        '''Handle user notification on context change event.'''
        context = self._session.get('Context', context_id)
        parents = ' / '.join([c['name'] for c in context['link']])
        QtWidgets.QMessageBox.information(
            self,
            'Context Changed',
            'You have now changed context to :{0}'.format(parents)
        )
