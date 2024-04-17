# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.progress import ProgressWidget
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread
from ftrack_qt.utils.widget import build_progress_data
from ftrack_constants import status as status_constants


class StandardStyleTestDialog(BaseContextDialog):
    '''Default Framework Opener dialog'''

    name = 'framework_standard_style_test_dialog'
    tool_config_type_filter = ['opener']
    ui_type = 'qt'
    run_button_title = 'OPEN'

    def __init__(
        self,
        event_manager,
        client_id,
        connect_methods_callback,
        connect_setter_property_callback,
        connect_getter_property_callback,
        dialog_options,
        parent=None,
    ):
        '''
        Initialize Mixin class opener dialog. It will load the qt dialog and
        mix it with the framework dialog.
        *event_manager*: instance of
        :class:`~ftrack_framework_core.event.EventManager`
        *client_id*: Id of the client that initializes the current dialog
        *connect_methods_callback*: Client callback method for the dialog to be
        able to execute client methods.
        *connect_setter_property_callback*: Client callback property setter for
        the dialog to be able to read client properties.
        *connect_getter_property_callback*: Client callback property getter for
        the dialog to be able to write client properties.
        *dialog_options*: Dictionary of arguments passed on to configure the
        current dialog.
        '''

        super(StandardStyleTestDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )

    def pre_build_ui(self):
        pass

    def build_ui(self):
        self.setWindowTitle("Style Test Dialog")

        # Create the scroll area and the widget that will contain all other widgets
        scroll_area = QtWidgets.QScrollArea(self)
        container_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container_widget)

        # Add QPushButton
        button = QtWidgets.QPushButton("Test Button")
        layout.addWidget(button)

        # Add borderless QPushButton
        borderless_button = QtWidgets.QPushButton("Borderless Button")
        borderless_button.setProperty('borderless', True)
        layout.addWidget(borderless_button)

        # Add filled QPushButton
        filled_button = QtWidgets.QPushButton("filled Button")
        filled_button.setProperty('filled', True)
        layout.addWidget(filled_button)

        # Button to trigger MessageBox
        msg_button = QtWidgets.QPushButton("Show MessageBox")
        msg_button.clicked.connect(self.show_message_box)
        layout.addWidget(msg_button)

        # Button to trigger ProgressWidget
        prgs_button = QtWidgets.QPushButton("Show ProgressWidget")
        prgs_button.clicked.connect(self.show_progress_widget)
        layout.addWidget(prgs_button)

        # Button to update status ProgressWidget
        prgs_update_button = QtWidgets.QPushButton(
            "Update status ProgressWidget"
        )
        prgs_update_button.clicked.connect(self.update_progress_widget_status)
        layout.addWidget(prgs_update_button)

        # Add QCheckBox
        checkbox = QtWidgets.QCheckBox("Test Checkbox")
        layout.addWidget(checkbox)

        # Add QComboBox
        combobox = QtWidgets.QComboBox()
        combobox.addItems(["Option 1", "Option 2", "Option 3"])
        layout.addWidget(combobox)

        # Add QFrame
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Box)
        layout.addWidget(frame)

        # Add selectable QFrame
        selectable_frame = QtWidgets.QFrame()
        selectable_frame.setFrameShape(QtWidgets.QFrame.Box)
        selectable_frame.setProperty('selectable', True)
        layout.addWidget(selectable_frame)

        # Add QLabel
        label = QtWidgets.QLabel("Test Label")
        layout.addWidget(label)

        # Add h1 QLabel
        h1_label = QtWidgets.QLabel("Test h1 Label")
        h1_label.setProperty('h1', True)
        layout.addWidget(h1_label)

        # Add h2 QLabel
        h2_label = QtWidgets.QLabel("Test h2 Label")
        h2_label.setProperty('h2', True)
        layout.addWidget(h2_label)

        # Add h3 QLabel
        h3_label = QtWidgets.QLabel("Test h3 Label")
        h3_label.setProperty('h3', True)
        layout.addWidget(h3_label)

        # Add secondary QLabel
        secondary_label = QtWidgets.QLabel("Test secondary Label")
        secondary_label.setProperty('secondary', True)
        layout.addWidget(secondary_label)

        # Add inactive QLabel
        inactive_label = QtWidgets.QLabel("Test inactive Label")
        inactive_label.setProperty('inactive', True)
        layout.addWidget(inactive_label)

        # Add secondary_inactive QLabel
        secondary_inactive_label = QtWidgets.QLabel(
            "Test secondary_inactive Label"
        )
        secondary_inactive_label.setProperty('secondary_inactive', True)
        layout.addWidget(secondary_inactive_label)

        # Add highlighted QLabel
        highlighted_label = QtWidgets.QLabel("Test highlighted Label")
        highlighted_label.setProperty('highlighted', True)
        layout.addWidget(highlighted_label)

        # Add QLineEdit
        lineedit = QtWidgets.QLineEdit("Test Line Edit")
        lineedit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        layout.addWidget(lineedit)

        # Add QListWidget
        list_widget = QtWidgets.QListWidget()
        list_widget.addItems(["Item 1", "Item 2", "Item 3"])
        layout.addWidget(list_widget)

        # Add QProgressBar
        progress = QtWidgets.QProgressBar()
        progress.setValue(50)
        layout.addWidget(progress)

        # Add QRadioButton
        radiobutton = QtWidgets.QRadioButton("Test Radio Button")
        layout.addWidget(radiobutton)

        # Add QTabBar
        tab_bar = QtWidgets.QTabBar()
        tab_bar.addTab("Tab 1")
        tab_bar.addTab("Tab 2")
        layout.addWidget(tab_bar)

        # Add QTextEdit
        text_edit = QtWidgets.QTextEdit("Test Text Edit")
        layout.addWidget(text_edit)

        # Add QTableWidget
        table_widget = QtWidgets.QTableWidget(2, 2)
        layout.addWidget(table_widget)

        # Add ftrack LineWidget
        from ftrack_qt.widgets.lines import LineWidget

        line_widget = LineWidget()
        layout.addWidget(line_widget)

        # Add ftrack progress widget
        self._progress_widget = ProgressWidget(
            'open',
            build_progress_data(self.filtered_tool_configs["opener"][0]),
        )
        self.header.set_widget(self._progress_widget.status_widget)

        # After adding all widgets
        scroll_area.setWidget(container_widget)
        scroll_area.setWidgetResizable(True)  # Make the scroll area resizable

        self.tool_widget.layout().addWidget(scroll_area)

    def show_message_box(self):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText("This is a message box for testing styles.")
        msg_box.exec_()

    def post_build_ui(self):
        pass

    def show_progress_widget(self):
        self._progress_widget.run(self)

    def update_progress_widget_status(self):
        for idx, status in enumerate(status_constants.STATUS_LIST):
            if self._progress_widget.status == status:
                if (idx + 1) == len(status_constants.STATUS_LIST):
                    next_idx = 0
                else:
                    next_idx = idx + 1
                self._progress_widget.update_status(
                    status_constants.STATUS_LIST[next_idx],
                    status_constants.STATUS_LIST[next_idx],
                )
                return

    def _on_run_button_clicked(self):
        '''(Override) Drive the progress widget'''
        pass

    @invoke_in_qt_main_thread
    def plugin_run_callback(self, log_item):
        '''(Override) Pass framework log item to the progress widget'''
        pass

    def closeEvent(self, event):
        '''(Override) Close the context and progress widgets'''
        if self._context_selector:
            self._context_selector.teardown()
        if self._progress_widget:
            self._progress_widget.teardown()
            self._progress_widget.deleteLater()
        super(StandardStyleTestDialog, self).closeEvent(event)
