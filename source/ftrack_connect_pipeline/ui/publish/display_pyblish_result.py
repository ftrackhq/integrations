# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtWidgets

import ftrack_connect_pipeline.ui.widget.item_list


class PyblishResult(QtWidgets.QWidget):
    '''Represents a pyblish result.'''

    def __init__(self, item):
        '''Instantiate from *item*.'''
        super(PyblishResult, self).__init__()

        self.setLayout(QtWidgets.QHBoxLayout())

        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())

        main_info = ''
        if item['error']:
            main_info += '<b>{0}: {1}</b>'.format(
                type(item['error']).__name__, item['error']
            )

        main_info += ' ' + item['plugin'].__name__
        widget.layout().addWidget(QtWidgets.QLabel(main_info))
        widget.layout().addWidget(
            QtWidgets.QLabel(
                'Duration: {0}, Running for instance: {1}'.format(
                    round(item['duration'], 4), item['instance']
                )
            )
        )

        number_of_logs = len(item['records'])
        if item['error']:
            number_of_logs += 1

        button = QtWidgets.QPushButton(
            'Show logs ({0})'.format(number_of_logs)
        )
        button.clicked.connect(
            self._on_button_clicked
        )
        if item['error']:
            button.setStyleSheet('''
                QWidget {
                    background-color: #f05b48;
                }
            ''')
        self.layout().addWidget(widget, stretch=1)
        self.layout().addWidget(button)

        self.item = item

    def _on_button_clicked(self, *args, **kwargs):
        '''Handle button clicked event.'''
        error = self.item.get('error')
        report_items = []
        if error:
            report_items.append(
                '{0}: {1}'.format(type(error).__name__, error)
            )
            report_items.append(str(self.item['error'].traceback))
            report_items.append(30 * '-')

        for record in self.item['records']:
            report_items.append(
                '{record.funcName}|{record.asctime}: {record.message}'.format(
                    record=record
                )
            )

        dialog = QtWidgets.QDialog()
        dialog.setMinimumSize(800, 600)
        dialog.setLayout(QtWidgets.QVBoxLayout())

        log_output_widget = QtWidgets.QTextEdit()
        log_output_widget.setReadOnly(True)

        log_output_widget.append('<br />'.join(report_items))
        font = log_output_widget.font()
        font.setFamily('Courier')
        font.setPointSize(10)

        dialog.layout().addWidget(log_output_widget)
        dialog.exec_()


class Dialog(QtWidgets.QDialog):
    '''Dialog to inspect detailed pyblish results.'''

    def __init__(self, results):
        '''Instantiate and show results.'''
        super(Dialog, self).__init__()
        self.setMinimumSize(600, 600)
        main_layout = QtWidgets.QVBoxLayout(self)
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
