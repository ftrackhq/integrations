# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtWidgets, QtCore


class EntityPath(QtWidgets.QTextEdit):
    '''Entity path widget.'''
    path_ready = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Instantiate the entity path widget.'''
        super(EntityPath, self).__init__(*args, **kwargs)
        self.setReadOnly(True)

        self.post_build()

    def post_build(self):
        self.path_ready.connect(self.on_path_ready)

    def setEntity(self, entity):
        '''Set the *entity* for this widget.'''
        if not entity:
            return

        parent = entity['parent']
        parents = [entity]

        while parent is not None:
            parents.append(parent)
            parent = parent['parent']

        parents.reverse()

        self.path_ready.emit(parents)

    def _set_html(self, data):
        table = """
            <table width="100%">
            <tr><th colspan="2">Info</th></tr>
            {}
            </table>
        """
        lines = []
        for datum in data:

            line = "<tr><td>{0}</td><td>{1}</td ></tr>".format(datum.entity_type, datum['name'])
            lines.append(line)

        result = table.format(''.join(lines))
        print(result)
        return result

    def on_path_ready(self, parents):
        '''Set current path to *names*.'''

        html = self._set_html(parents)
        self.setHtml(html)
