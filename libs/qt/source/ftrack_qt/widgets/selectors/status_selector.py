# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtGui, QtCore, QtWidgets

from ftrack_utils.threading import BaseThread


class StatusSelector(QtWidgets.QComboBox):
    _status_colors = {}

    statusesFetched = QtCore.Signal(object)

    @property
    def session(self):
        return self._session

    @property
    def context_id(self):
        return self._context_id

    def __init__(self, session, context_id, parent=None):
        super(StatusSelector, self).__init__(parent=parent)
        self._session = session
        self._context_id = context_id

        self.setEditable(False)
        self.setMinimumWidth(150)
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)

        thread = BaseThread(
            name='fetch_status_thread',
            target=self._fetch_statuses,
            callback=self._on_status_fetched,
            target_args=(),
        )
        thread.start()

    def _on_status_fetched(self, statuses):
        '''Set statuses on the combo box'''
        self.set_statuses(statuses)
        if statuses:
            self.on_status_changed(statuses[0]['id'])

    def _fetch_statuses(self):
        '''Returns the status of the selected assetVersion'''
        context_entity = self.session.query(
            'select link, name, parent, parent.name from Context where id '
            'is "{}"'.format(self.context_id)
        ).one()

        project = self.session.query(
            'select name, parent, parent.name from Context where id is "{}"'.format(
                context_entity['link'][0]['id']
            )
        ).one()

        schema = project['project_schema']
        statuses = schema.get_statuses('AssetVersion')
        return statuses

    def set_statuses(self, statuses):
        '''Set statuses on the combo box'''
        # We are now in the main thread
        for index, status in enumerate(statuses):
            self.addItem(status['name'].upper(), status['id'])
            self._status_colors[status['id']] = status['color']

    def on_status_changed(self, status_id):
        '''Update my style to reflect status color.'''
        self.setStyleSheet(
            '''
            QComboBox {
                border-radius: 3px;
                color: %s;
            }
        '''
            % (self._status_colors.get(status_id) or '#303030',)
        )
