# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtWidgets

import ftrack_connect_pipeline
import ftrack_connect_pipeline.ui.model.log_table
from ftrack_connect_pipeline.util import (
    extract_error_message_from_record,
    extract_plugin_name_from_record
)


class Dialog(QtWidgets.QDialog):
    '''Dialog to inspect detailed pyblish results.'''

    def __init__(self, results):
        '''Instantiate and show results.'''
        super(Dialog, self).__init__()
        self.setObjectName('ftrack-result-dialog')
        self.setMinimumSize(1080, 720)
        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)

        filter_layout = QtWidgets.QHBoxLayout()
        filter_label = QtWidgets.QLabel('Filter log')
        self.filter_field = QtWidgets.QLineEdit()
        self.filter_field.setObjectName('ftrack-log-filter-field')
        self.filter_field.textChanged.connect(self.on_search)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_field)
        main_layout.addLayout(filter_layout)

        log_list = QtWidgets.QTableView()
        log_list.verticalHeader().hide()

        log_list.setObjectName('ftrack-log-view')
        log_list.setAlternatingRowColors(True)
        log_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        log_list.horizontalHeader().setStretchLastSection(True)
        log_items = self._parse_results(results)

        log_model = ftrack_connect_pipeline.ui.model.log_table.LogTableModel(
            self, log_items
        )
        self.log_sort_model = ftrack_connect_pipeline.ui.model.log_table.FilterProxyModel()
        self.log_sort_model .setDynamicSortFilter(True)
        self.log_sort_model .setSourceModel(log_model)
        log_list.setModel(self.log_sort_model)

        main_layout.addWidget(log_list)

        open_log_folder_button = QtWidgets.QPushButton('Open log directory')
        open_log_folder_button.clicked.connect(self._on_logging_button_clicked)
        main_layout.addWidget(open_log_folder_button)

    def _parse_results(self, results):
        '''Parse raw results and return a list of LogItem.'''
        items = []
        for result in results:
            plugin_name = extract_plugin_name_from_record(result)

            if result['success']:
                # create entry for success entry
                for record in result['records']:
                    new_item = ftrack_connect_pipeline.ui.model.log_table.LogItem()
                    new_item.status = 'OK'
                    new_item.record = record.message
                    new_item.time = record.asctime
                    new_item.method = record.funcName
                    new_item.duration = result['duration']
                    new_item.name = plugin_name
                    items.append(new_item)
            else:
                new_item = ftrack_connect_pipeline.ui.model.log_table.LogItem()
                new_item.status = 'ERROR'
                new_item.record = extract_error_message_from_record(result)
                new_item.time = ''
                new_item.method = ''
                new_item.duration = result['duration']
                new_item.name = plugin_name
                items.append(new_item)

        return items

    def _on_logging_button_clicked(self):
        '''Handle logging button clicked.'''
        directory = ftrack_connect_pipeline.config.get_log_directory()
        ftrack_connect_pipeline.util.open_directory(directory)

    def on_search(self):
        '''Search in the current model.'''
        value = self.filter_field.text()
        self.log_sort_model.setFilterWildcard(value)
