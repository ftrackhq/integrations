# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile

from PySide2 import QtGui, QtWidgets

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NodegraphThumbnailExporterPlugin(BasePlugin):
    '''Save a screenshot of the nodegraph to temp location for publish'''

    name = 'nodegraph_thumbnail_exporter'

    def findviewer(self):
        stack = QtWidgets.QApplication.topLevelWidgets()
        viewers = []
        while stack:
            widget = stack.pop()
            if widget.windowTitle().startswith('Node'):
                viewers.append(widget)
            stack.extend(c for c in widget.children() if c.isWidgetType())
        return viewers

    def getRelativeFrameGeometry(self, widget):
        fg = widget.frameGeometry()
        left = top = 0
        while True:
            g = widget.geometry()
            left += g.left()
            top += g.top()
            widget = widget.parent()
            if widget is None:
                break
        self.logger.debug(
            "Grab node graph thumbnail - relative frame geometry; g.left: {}, g.top: {}".format(
                left, top
            )
        )
        return fg.translated(left, top)

    def screenCaptureWidget(self, widget, filename, file_format='png'):
        rfg = self.getRelativeFrameGeometry(widget)
        pixmap = QtGui.QPixmap.grabWindow(
            widget.winId(),
            rfg.left(),
            rfg.top(),
            rfg.width(),
            rfg.height(),
        )
        self.logger.debug(
            "Grab node graph thumbnail - screen; left: {}, top: {}, width: {}, height: {}".format(
                rfg.left(), rfg.top(), rfg.width(), rfg.height()
            )
        )
        pixmap.save(filename, fileformat)

    def run(self, store):
        '''
        Expects collected_script in the <component_name> key of the
        given *store*, stores the exported thumbnail path in the :obj:`store`
        '''
        component_name = self.options.get('component')
        try:
            view = self.findviewer()[1]

            thumbnail_path = tempfile.NamedTemporaryFile(
                delete=False, suffix='.png'
            ).name

            self.screenCaptureWidget(view, thumbnail_path)
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception exporting the node graph thumbnail: {e}'
            )

        store['components'][component_name]['exported_path'] = thumbnail_path
