# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import xml.etree.ElementTree as ET
from xml.sax.saxutils import unescape
import os
import tempfile

import hou

created_widgets = dict()


# Dock widget in Houdini
def dock_houdini_right(widget):
    '''Dock *widget* to the right side of Houdini.'''
    class_name = widget.__class__.__name__

    if class_name not in globals():
        globals()[class_name] = lambda *args, **kwargs: widget

    created_widgets[class_name] = widget

    panel_xml = _generate_pypanel_xml(class_name)
    xml = unescape(ET.tostring(panel_xml).decode())

    xml_path = os.path.join(
        tempfile.gettempdir(),
        'ftrack',
        'connect',
        '{}.pypanel'.format("Title 1"),
    )

    if not os.path.exists(os.path.dirname(xml_path)):
        os.makedirs(os.path.dirname(xml_path))

    with open(xml_path, "w") as xml_file_handle:
        xml_file_handle.write(xml)
        xml_file_handle.close()

    hou.pypanel.installFile(xml_path)

    panel_interface = None

    try:
        for interface, value in hou.pypanel.interfaces().items():
            if interface == "ftrack Publish panel":
                panel_interface = value
                break
    except hou.OperationFailed as e:
        hou.ui.displayMessage("Something wrong with Python Panel")

    main_tab = hou.ui.curDesktop().findPaneTab("Ftrack_ID")
    if main_tab:
        panel = main_tab.pane().createTab(hou.paneTabType.PythonPanel)
        panel.showToolbar(True)
        panel.setActiveInterface(panel_interface)
    else:
        if panel_interface:
            hou.hscript('pane -S -m pythonpanel -o -n {}'.format("Ftrack_ID"))
            panel = hou.ui.curDesktop().findPaneTab("Ftrack_ID")
            panel.showToolbar(True)
            panel.setActiveInterface(panel_interface)


def run_in_main_thread(f):
    '''Make sure a function runs in the main Houdini thread.'''

    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            pass
            # return houdini_utils.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated


def _generate_pypanel_xml(widget_name):
    '''Write temporary xml file for pypanel'''

    root = ET.Element("pythonPanelDocument")
    interface = ET.SubElement(root, "interface")
    interface.set("name", "ftrack Publish panel")
    interface.set("label", "ftrack Publish panel")
    interface.set("icon", "MISC_python")
    interface.set("help_url", "")
    script = ET.SubElement(interface, "script")
    script.text = """
<![CDATA[
# import hou
# hou.ui.displayMessage(globals())
from PySide2.QtWidgets import QWidget, QVBoxLayout
import __main__
layout = QVBoxLayout()
layout.addWidget(__main__.ftrack_framework_houdini.utils.created_widgets['{}'])
def onCreateInterface():
    widget = QWidget()
    widget.setLayout(layout)
    return widget
]]>
""".format(
        widget_name
    )
    help = ET.SubElement(interface, "help")
    help.text = "<![CDATA[]]>"

    return root
