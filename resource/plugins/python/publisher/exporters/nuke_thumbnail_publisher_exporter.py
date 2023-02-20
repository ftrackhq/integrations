# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

import tempfile
import nuke

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class NukeThumbnailPublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    '''Nuke thumbnail exporter plugin'''

    plugin_name = 'nuke_thumbnail_publisher_exporter'

    def render_thumbnail(self, context_data=None, data=None, options=None):
        '''Export a thumbnail from Nuke from collected node with *data* based on *options*'''

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        node_name = collected_objects[0]
        input_node = nuke.toNode(node_name)
        selected_nodes = nuke.selectedNodes()
        nuke_utils.cleanSelection()

        write_node = nuke.createNode('Write')
        write_node.setInput(0, input_node)

        # create reformat dcc_object
        reformat_node = nuke.nodes.Reformat()
        reformat_node['type'].setValue("to box")
        reformat_node['box_width'].setValue(200.0)

        # connect given write dcc_object to reformat.
        reformat_node.setInput(0, write_node)

        # create new write for reformat and connect it.
        new_write_node = nuke.nodes.Write()
        new_write_node.setInput(0, reformat_node)

        file_name = tempfile.NamedTemporaryFile(
            delete=False, suffix='.png'
        ).name

        new_write_node['file'].setValue(file_name.replace('\\', '/'))
        new_write_node['file_type'].setValue('png')
        # render thumbnail
        curFrame = int(nuke.knob("frame"))

        nuke.execute(new_write_node, curFrame, curFrame)

        # delete thumbnail network after render
        nuke.delete(reformat_node)
        nuke.delete(new_write_node)

        # delete temporal write node
        nuke.delete(write_node)
        # restore selection
        nuke_utils.cleanSelection()
        for node in selected_nodes:
            node['selected'].setValue(True)

        return [file_name]

    def grab_node_graph_thumbnail(
        self, context_data=None, data=None, options=None
    ):
        '''Grab a screenshot of the node graph and use as thumbnail'''

        from PySide2 import QtGui, QtWidgets

        def findviewer():
            stack = QtWidgets.QApplication.topLevelWidgets()
            viewers = []
            while stack:
                widget = stack.pop()
                if widget.windowTitle().startswith('Node'):
                    viewers.append(widget)
                stack.extend(c for c in widget.children() if c.isWidgetType())
            print(viewers)
            return viewers

        def getRelativeFrameGeometry(widget):
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

        def screenCaptureWidget(widget, filename, fileformat='png'):
            rfg = getRelativeFrameGeometry(widget)
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

        view = findviewer()[1]

        file_name = tempfile.NamedTemporaryFile(
            delete=False, suffix='.png'
        ).name

        screenCaptureWidget(view, file_name)

        return [file_name]

    def run(self, context_data=None, data=None, options=None):
        target = options.get('target') or 'render_from_node'
        if target == 'node_graph':
            return self.grab_node_graph_thumbnail(context_data, data, options)
        elif target == 'render_from_node':
            return self.render_thumbnail(context_data, data, options)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeThumbnailPublisherExporterPlugin(api_object)
    plugin.register()
