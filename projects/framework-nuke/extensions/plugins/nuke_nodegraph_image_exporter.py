# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from PySide2 import QtGui, QtWidgets

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_nuke.utils import (
    find_nodegraph_viewer,
    activate_nodegraph_viewer,
)


class NukeNodegraphImageExporterPlugin(BasePlugin):
    '''Save an image of the nodegraph to temp location for publish'''

    name = 'nuke_nodegraph_image_exporter'

    def get_relative_frame_geometry(self, widget):
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
            "Grab node graph image - relative frame geometry; g.left: {}, g.top: {}".format(
                left, top
            )
        )
        return fg.translated(left, top)

    def screen_capture_widget(self, widget, filename, file_format='png'):
        '''Grab the viewer screenshot'''
        rfg = self.get_relative_frame_geometry(widget)
        pixmap = QtGui.QPixmap.grabWindow(
            widget.winId(),
            rfg.left(),
            rfg.top(),
            rfg.width(),
            rfg.height(),
        )
        self.logger.debug(
            "Grab node graph image - screen; left: {}, top: {}, width: {}, height: {}".format(
                rfg.left(), rfg.top(), rfg.width(), rfg.height()
            )
        )
        pixmap.save(filename, file_format)

    def run(self, store):
        '''
        Exports a png image of the node graph to the <component> key of the
        given *store*
        '''
        component_name = self.options.get('component')
        try:
            view = find_nodegraph_viewer()

        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception locating viewer to export: {e}'
            )

        try:
            image_path = get_temp_path(filename_extension='png')

            self.screen_capture_widget(view, image_path)
        except Exception as e:
            self.logger.exception(e)
            raise PluginExecutionError(
                f'Exception exporting the node graph image: {e}'
            )

        self.logger.debug(f'Exported node graph image to: {image_path}')

        store['components'][component_name]['exported_path'] = image_path
