# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

from PySide2 import QtGui, QtWidgets

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukeNodegraphThumbnailExporterPlugin(BasePlugin):
    '''Save a screenshot of the nodegraph to temp location for publish'''

    name = 'nuke_nodegraph_thumbnail_exporter'

    def findviewer(self):
        '''Find the nodegraph viewers by title'''
        stack = QtWidgets.QApplication.topLevelWidgets()
        viewers = []
        while stack:
            widget = stack.pop()
            if widget.windowTitle().startswith('Node'):
                viewers.append(widget)
            stack.extend(c for c in widget.children() if c.isWidgetType())
        if len(viewers) <= 1:
            raise Exception(
                'Could not find node graph viewer to export thumbnail from'
            )
        return viewers[1]

    def getRelativeFrameGeometry(self, widget):
        '''Get the viewer bounds'''
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
        '''Grab the viewer screenshot'''
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
        pixmap.save(filename, file_format)

    def run(self, store):
        '''
        Expects a thumbnail of the node graph to the <component> key of the
        given *store*
        '''
        component_name = self.options.get('component')
        try:
            view = self.findviewer()

        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception locating viewer to export: {e}'
            )

        try:
            thumbnail_path = get_temp_path(filename_extension='.png')

            self.screenCaptureWidget(view, thumbnail_path)
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception exporting the node graph thumbnail: {e}'
            )

        self.logger.debug(
            f'Exported node graph thumbnail to: {thumbnail_path}'
        )

        store['components'][component_name]['exported_path'] = thumbnail_path
