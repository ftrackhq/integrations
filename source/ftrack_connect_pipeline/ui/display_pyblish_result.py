
from PySide import QtGui

import ftrack_connect_pipeline.ui.widget.item_list


class PyblishResult(QtGui.QWidget):
    '''Represents a pyblish result.'''

    def __init__(self, item):
        '''Instantiate from *item*.'''
        super(PyblishResult, self).__init__()

        self.setLayout(QtGui.QHBoxLayout())

        widget = QtGui.QWidget()
        widget.setLayout(QtGui.QVBoxLayout())

        main_info = ''
        if item['error']:
            self.setStyleSheet('''
                QWidget {
                    background-color: #f05b48;
                }
            ''')
            main_info += '{0}: {1}'.format(
                type(item['error']).__name__, item['error']
            )

        main_info += item['plugin'].__name__
        widget.layout().addWidget(QtGui.QLabel(main_info))
        widget.layout().addWidget(
            QtGui.QLabel(
                'Duraction: {0}, Running for instance: {1}'.format(
                    round(item['duration'], 4), item['instance']
                )
            )
        )

        number_of_logs = len(item['records'])
        if item['error']:
            number_of_logs += 1

        button = QtGui.QPushButton('Show logs ({0})'.format(number_of_logs))
        button.clicked.connect(
            self._on_button_clicked
        )
        self.layout().addWidget(widget, stretch=1)
        self.layout().addWidget(button)

        self.item = item

    def _on_button_clicked(self, *args, **kwargs):
        '''Handle button clicked event.'''
        report = ''
        if self.item['error']:
            report += str(self.item['error'].traceback)
            report += '<br />' + 30 * '-'

        logs_entries = []
        for record in self.item['records']:
            logs_entries.append(
                '{record.module} - {record.created}: {record.message}'.format(
                    record=record
                )
            )
        report += '<br />' + '<br />'.join(logs_entries)

        dialog = QtGui.QDialog()
        dialog.setMinimumSize(800, 600)
        dialog.setLayout(QtGui.QVBoxLayout())

        log_output = QtGui.QTextEdit()
        log_output.setReadOnly(True)

        log_output.append(report)
        font = log_output.font()
        font.setFamily("Courier")
        font.setPointSize(10)

        dialog.layout().addWidget(log_output)
        dialog.exec_()


class Dialog(QtGui.QDialog):
    '''Dialog to inspect detailed pyblish results.'''

    def __init__(self, results):
        '''Instantiate and show results.'''
        super(Dialog, self).__init__()
        self.setMinimumSize(500, 600)
        main_layout = QtGui.QVBoxLayout(self)
        self.setLayout(main_layout)

        list_widget = ftrack_connect_pipeline.ui.widget.item_list.ItemList(
            widgetFactory=self.create_widget,
            widgetItem=lambda widget: widget.item
        )
        main_layout.addWidget(list_widget)
        for item in results:
            list_widget.addItem(item)

    def create_widget(self, item):
        '''Create widget from *item*.'''
        return PyblishResult(item)
