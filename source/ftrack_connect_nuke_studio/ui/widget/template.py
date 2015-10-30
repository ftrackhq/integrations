# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from PySide import QtCore
from PySide import QtGui


import ftrack_connect_nuke_studio.template as template_manager


class TemplateDelegate(QtGui.QStyledItemDelegate):

    def paint(self, painter, options, index):
        '''Override paint to display title and description.'''
        data = self.parent().itemData(index.row())

        style = QtGui.QApplication.style()
        style.drawControl(QtGui.QStyle.CE_ItemViewItem, options, painter)
        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()

        doc = QtGui.QTextDocument()
        doc.setHtml('<b>{0}</b><br>{1}<br>'.format(
            data['name'], data['description']
        ))
        doc.adjustSize()
        options.text = ''
        textRect = style.subElementRect(
            QtGui.QStyle.SE_ItemViewItemText, options, None
        )

        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))

        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, options, index):
        '''Returns the size needed to display the item in a QSize object.'''
        data = self.parent().itemData(index.row())
        self.initStyleOption(options, index)

        doc = QtGui.QTextDocument()
        doc.setHtml('<b>{0}</b><br>{1}<br>'.format(
            data['name'], data['description']
        ))
        doc.adjustSize()

        return QtCore.QSize(doc.idealWidth(), doc.size().height())


class Template(QtGui.QComboBox):
    '''Template combobox.'''

    def __init__(self, project, parent=None):
        super(Template, self).__init__(parent=parent)

        delegate = TemplateDelegate(self)
        self.setItemDelegate(delegate)

        self._templates = template_manager.available_templates(project)

        default_index = 0
        for index, template in enumerate(self._templates):
            self.addItem(template['name'])
            self.setItemData(
                index, template
            )

            if template.get('default'):
                default_index = index

        if default_index:
            self.setCurrentIndex(default_index)

    def selected_template(self):
        '''Return currently selected template.'''
        return self.itemData(self.currentIndex())
