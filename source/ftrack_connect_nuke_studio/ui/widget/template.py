# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from PySide import QtCore
from PySide import QtGui

import ftrack_connect_nuke_studio.template as template_manager


class Template(QtGui.QComboBox):
    '''Template combobox.'''

    def __init__(self, project, parent=None):
        super(Template, self).__init__(parent=parent)

        self._templates = template_manager.available_templates(project)

        default_index = 0
        for index, template in enumerate(self._templates):
            self.addItem(template['name'], userData=template)
            self.setItemData(
                index, template['description'], role=QtCore.Qt.ToolTipRole
            )

            if template.get('default'):
                default_index = index

        if default_index:
            self.setCurrentIndex(default_index)

    def selected_template(self):
        '''Return currently selected template.'''
        return self.itemData(self.currentIndex())
