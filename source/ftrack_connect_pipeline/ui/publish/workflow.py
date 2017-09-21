# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import sys
import functools
import time
import webbrowser

from QtExt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline.ui.widget.overlay import BusyOverlay
from ftrack_connect_pipeline.ui.widget.overlay import Overlay
from ftrack_connect_pipeline.ui.widget.field import textarea
from ftrack_connect_pipeline.ui.usage import send_event as send_usage
from ftrack_connect_pipeline.ui.style import OVERLAY_DARK_STYLE
from ftrack_connect_pipeline.ui import resource

import ftrack_connect_pipeline.util


class CreateAssetTypeOverlay(Overlay):
    '''Create asset type overlay.'''

    asset_creation_failed = QtCore.Signal()

    def __init__(self, session, parent):
        '''Instantiate with *session*.'''
        super(CreateAssetTypeOverlay, self).__init__(parent=parent)
        self.session = session

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        icon = QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor')
        icon = icon.scaled(
            QtCore.QSize(85, 85),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.ftrack_icon = QtWidgets.QLabel()
        self.ftrack_icon.setPixmap(icon)

        self.main_layout.addStretch(1)
        self.main_layout.insertWidget(
            1, self.ftrack_icon, alignment=QtCore.Qt.AlignCenter
        )
        self.main_layout.addStretch(1)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # create asset type widget
        self.create_asset_widget = QtWidgets.QFrame()
        self.create_asset_widget.setVisible(False)

        create_asset_layout = QtWidgets.QVBoxLayout()
        create_asset_layout.setContentsMargins(20, 20, 20, 20)
        create_asset_layout.addStretch(1)
        buttons_layout = QtWidgets.QHBoxLayout()
        self.create_asset_widget.setLayout(create_asset_layout)

        self.create_asset_label_top = QtWidgets.QLabel()

        self.create_asset_label_bottom = QtWidgets.QLabel(
            '<h4>Do you want to create one ?</h4>'
        )

        create_asset_layout.insertWidget(
            1,
            self.create_asset_label_top,
            alignment=QtCore.Qt.AlignCenter
        )
        create_asset_layout.insertWidget(
            2,
            self.create_asset_label_bottom,
            alignment=QtCore.Qt.AlignCenter
        )
        self.create_asset_button = QtWidgets.QPushButton('Create')
        self.cancel_asset_button = QtWidgets.QPushButton('Cancel')
        create_asset_layout.addLayout(buttons_layout)
        buttons_layout.addWidget(self.create_asset_button)
        buttons_layout.addWidget(self.cancel_asset_button)

        # result create asset type
        self.create_asset_widget_result = QtWidgets.QFrame()
        self.create_asset_widget_result.setVisible(False)

        create_asset_layout_result = QtWidgets.QVBoxLayout()
        create_asset_layout_result.setContentsMargins(20, 20, 20, 20)
        create_asset_layout_result.addStretch(1)

        self.create_asset_widget_result.setLayout(create_asset_layout_result)
        self.create_asset_label_result = QtWidgets.QLabel()
        self.continue_button = QtWidgets.QPushButton('Continue')

        create_asset_layout_result.insertWidget(
            1,
            self.create_asset_label_result,
            alignment=QtCore.Qt.AlignCenter
        )

        create_asset_layout_result.insertWidget(
            2,
            self.continue_button,
            alignment=QtCore.Qt.AlignCenter
        )

        # error on create asset
        self.create_asset_widget_error = QtWidgets.QFrame()
        self.create_asset_widget_error.setVisible(False)

        create_asset_layout_error = QtWidgets.QVBoxLayout()
        create_asset_layout_error.setContentsMargins(20, 20, 20, 20)
        create_asset_layout_error.addStretch(1)

        self.create_asset_widget_error.setLayout(create_asset_layout_error)
        self.create_asset_label_error = QtWidgets.QLabel()
        self.close_button = QtWidgets.QPushButton('Close')

        create_asset_layout_error.insertWidget(
            1,
            self.create_asset_label_error,
            alignment=QtCore.Qt.AlignCenter
        )

        create_asset_layout_error.insertWidget(
            2,
            self.close_button,
            alignment=QtCore.Qt.AlignCenter
        )

        # parent all.
        self.main_layout.addWidget(self.create_asset_widget)
        self.main_layout.addWidget(self.create_asset_widget_result)
        self.main_layout.addWidget(self.create_asset_widget_error)

        self.main_layout.addStretch(1)

        # signals
        self.create_asset_button.clicked.connect(self.on_create_asset)
        self.continue_button.clicked.connect(self.on_continue)
        self.close_button.clicked.connect(self.on_fail)
        self.cancel_asset_button.clicked.connect(self.on_fail)

    def populate(self, asset_type_short, asset_type):
        '''Populate with *asset_type_short* and *asset_type*.'''
        self.create_asset_widget.setVisible(True)
        self.create_asset_widget_result.setVisible(False)
        self.create_asset_widget_error.setVisible(False)

        self.asset_type = asset_type
        self.asset_type_short = asset_type_short

        self.create_asset_label_top.setText(
            '<h2>The required asset type {0} ({1}) does not exist on your '
            'ftrack instance.</h2>'.format(
                self.asset_type, self.asset_type_short
            )
        )

    def on_fail(self):
        '''Handle fail.'''
        self.asset_creation_failed.emit()
        self.setVisible(False)

    def on_continue(self):
        '''Handle continue.'''
        self.setVisible(False)

    def on_create_asset(self):
        '''Handle asset created.'''
        result = ftrack_connect_pipeline.util.create_asset_type(
            self.session, self.asset_type, self.asset_type_short
        )

        if result['status']:
            self.create_asset_widget.setVisible(False)
            self.create_asset_label_result.setText(
                '<center><h2>{0}</h2></center>'.format(result['message'])
            )
            self.create_asset_widget_result.setVisible(True)
        else:
            self.create_asset_widget.setVisible(False)
            self.create_asset_label_error.setText(
                '<center><h2>{0}</h2></center>'.format(result['message'])
            )
            self.create_asset_widget_error.setVisible(True)


class PublishResult(Overlay):
    '''Publish result overlay.'''

    def __init__(self, session, parent):
        '''Instantiate publish result overlay.'''
        super(PublishResult, self).__init__(parent=parent)
        self.session = session
        self.activeWidget = None
        self.setLayout(QtWidgets.QVBoxLayout())

    def create_overlay_widgets(self, congrat_text, success_text):
        '''Create overlay widgets to report publish result.'''

        self.activeWidget = QtWidgets.QWidget()
        self.activeWidget.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.activeWidget)
        main_layout = self.activeWidget.layout()

        icon = QtGui.QPixmap(':ftrack/image/default/ftrackLogoLabelNew')
        icon = icon.scaled(
            QtCore.QSize(85, 85),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )

        self.ftrack_icon = QtWidgets.QLabel()
        self.ftrack_icon.setPixmap(icon)

        main_layout.addStretch(1)
        main_layout.insertWidget(
            1, self.ftrack_icon, alignment=QtCore.Qt.AlignCenter
        )

        congrat_label = QtWidgets.QLabel(congrat_text)
        congrat_label.setAlignment(QtCore.Qt.AlignCenter)

        success_label = QtWidgets.QLabel(success_text)
        success_label.setAlignment(QtCore.Qt.AlignCenter)

        main_layout.addWidget(congrat_label)
        main_layout.addWidget(success_label)
        main_layout.addStretch(1)

        buttons_layout = QtWidgets.QHBoxLayout()

        main_layout.addLayout(buttons_layout)

        self.details_button = QtWidgets.QPushButton('Details')
        buttons_layout.addWidget(self.details_button)
        self.details_button.clicked.connect(self.on_show_details)

        if self.details_window_callback is None:
            self.details_button.setDisabled(True)

        self.open_in_ftrack = QtWidgets.QPushButton('Open in ftrack')
        buttons_layout.addWidget(self.open_in_ftrack)
        self.open_in_ftrack.clicked.connect(self.on_open_in_ftrack)

        if self.asset_version is None:
            self.open_in_ftrack.setDisabled(True)

    def create_validate_failed_overlay_widgets(self, label, failed_validators):
        '''Create overlay widgets to report validation failures.'''
        congrat_text = '<h2>Validation Failed!</h2>'
        success_text = 'Your <b>{0}</b> failed to validate.'.format(label)

        self.activeWidget = QtWidgets.QWidget()
        self.activeWidget.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.activeWidget)
        main_layout = self.activeWidget.layout()

        main_layout.addStretch(1)

        congrat_label = QtWidgets.QLabel(congrat_text)
        congrat_label.setAlignment(QtCore.Qt.AlignCenter)

        success_label = QtWidgets.QLabel(success_text)
        success_label.setAlignment(QtCore.Qt.AlignCenter)

        main_layout.addWidget(congrat_label)
        main_layout.addWidget(success_label)

        validators_table_container = QtWidgets.QWidget()
        table_layout = QtWidgets.QVBoxLayout()
        table_layout.setContentsMargins(15, 10, 15, 10)
        validators_table_container.setLayout(table_layout)

        validators_table = QtWidgets.QTableWidget()
        validators_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        validators_table.setSelectionMode(QtWidgets.QTableWidget.NoSelection)

        validators_table.setColumnCount(2)
        validators_table.setHorizontalHeaderLabels(['Validation', 'Error'])
        validators_table.horizontalHeader().setResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )
        validators_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        validators_table.horizontalHeader().setVisible(True)

        validators_table.setRowCount(len(failed_validators))
        validators_table.verticalHeader().setVisible(False)

        icon = QtGui.QIcon(':ftrack/image/dark/remove')
        font = QtGui.QFont()
        font.setBold(True)

        for row, validator in enumerate(failed_validators):
            item = QtWidgets.QTableWidgetItem(icon, validator[0])
            item.setFont(font)
            validators_table.setItem(row, 0, item)

            error_msg = validator[1]

            # Remove quotes from error message, if present.
            if (
                (error_msg[0] == error_msg[-1]) and
                error_msg.startswith(("'", '"'))
            ):
                error_msg = error_msg[1:-1]

            item = QtWidgets.QTableWidgetItem(error_msg)
            validators_table.setItem(row, 1, item)

        table_layout.addWidget(validators_table)
        main_layout.addWidget(validators_table_container)

        main_layout.addStretch(1)
        label = QtWidgets.QLabel('See details for more information.')
        label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(label)

        buttons_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        self.details_button = QtWidgets.QPushButton('Details')
        buttons_layout.addWidget(self.details_button)
        self.details_button.clicked.connect(self.on_show_details)

        self.close_button = QtWidgets.QPushButton('Close')
        buttons_layout.addWidget(self.close_button)
        self.close_button.clicked.connect(self.close_window_callback)

        if self.details_window_callback is None:
            self.details_button.setDisabled(True)

    def populate(
        self, label, details_window_callback, close_window_callback, result
    ):
        '''Populate with content.'''

        if self.activeWidget:
            self.layout().removeWidget(self.activeWidget)
            self.activeWidget.setParent(None)
            self.activeWidget = None

        self.details_window_callback = details_window_callback
        self.close_window_callback = close_window_callback

        self.asset_version = result.get('asset_version', None)
        success = result['success']

        if not success and result['stage'] == 'validation':
            self.create_validate_failed_overlay_widgets(
                label, result['errors']
            )
            return

        if success:
            congrat_text = '<h2>Publish Successful!</h2>'
            success_text = 'Your <b>{0}</b> has been successfully published.'
        else:
            congrat_text = '<h2>Publish Failed!</h2>'
            success_text = (
                'Your <b>{0}</b> failed to publish. '
                'See details for more information.')

        self.create_overlay_widgets(congrat_text, success_text.format(label))

    def on_show_details(self):
        '''Handle show of details.'''
        self.details_window_callback()

    def on_open_in_ftrack(self):
        '''Open result in ftrack.'''

        data = {
            'server_url': self.session.server_url,
            'version_id': self.asset_version['id'],
            'project_id': self.asset_version['link'][0]['id']
        }

        url_template = (
            '{server_url}/#slideEntityId={version_id}'
            '&slideEntityType=assetversion'
            '&view=versions_v1'
            '&itemId=projects'
            '&entityId={project_id}'
            '&entityType=show'
        ).format(**data)

        webbrowser.open_new_tab(url_template)


class SelectableItemWidget(QtWidgets.QListWidgetItem):
    '''A selectable item widget.'''

    def __init__(self, item):
        '''Instanstiate widget from *item*.'''
        super(SelectableItemWidget, self).__init__()
        self._item = item
        self.setText(item['label'])
        self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)

        self.setCheckState(
            QtCore.Qt.Checked if item.get('value') else QtCore.Qt.Unchecked
        )

    def item(self):
        '''Return pyblish instance.'''
        return self._item


class ListItemsWidget(QtWidgets.QListWidget):
    '''List of items that can be published.'''

    def __init__(self, items):
        '''Instanstiate and generate list from *items*.'''
        super(ListItemsWidget, self).__init__()
        self.setObjectName('ftrack-list-widget')
        for item in items:
            item = SelectableItemWidget(item)
            self.addItem(item)

    def paintEvent(self, event):
        '''Draw placeholder text.'''
        root_index = self.rootIndex()
        model = self.model()

        if model and model.rowCount(root_index):
            super(ListItemsWidget, self).paintEvent(event)
        else:
            painter = QtGui.QPainter(self.viewport())
            rect = self.rect()
            painter.drawText(
                rect,
                QtCore.Qt.AlignCenter,
                'No items found to publish'
            )

    def get_checked_items(self):
        '''Return checked items.'''
        checked_items = []
        for index in xrange(self.count()):
            widget_item = self.item(index)
            if widget_item.checkState() is QtCore.Qt.Checked:
                checked_items.append(widget_item.item())

        return checked_items

    def update_selection(self, new_selection):
        '''Update selection from *new_selection*.'''
        for index in xrange(self.count()):
            widget_item = self.item(index)
            item = widget_item.item()
            should_select = item['name'] in new_selection
            widget_item.setCheckState(
                QtCore.Qt.Checked if should_select else QtCore.Qt.Unchecked
            )


class ActionSettingsWidget(QtWidgets.QWidget):
    '''A widget to display settings.'''

    def __init__(self, data_dict, options):
        '''Instanstiate settings from *options*.'''
        super(ActionSettingsWidget, self).__init__()

        self.setLayout(QtWidgets.QFormLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        for option in options:
            type_ = option['type']
            label = option.get('label', '')
            name = option['name']
            value = option.get('value')
            empty_text = option.get('empty_text')
            if name in data_dict.get('options', {}):
                value = data_dict['options'][name]

            if value is not None and name not in data_dict:
                # Set default value from options.
                data_dict[name] = value

            field = None

            if type_ == 'group':
                nested_dict = data_dict[name] = dict()
                settings_widget = QtWidgets.QGroupBox(label)
                settings_widget.setLayout(QtWidgets.QVBoxLayout())
                settings_widget.layout().addWidget(
                    ActionSettingsWidget(
                        nested_dict, option.get('options', [])
                    )
                )
                self.layout().addRow(settings_widget)

            if type_ == 'boolean':
                field = QtWidgets.QCheckBox()
                if value is True:
                    field.setCheckState(QtCore.Qt.Checked)

                field.stateChanged.connect(
                    functools.partial(
                        self.update_on_change,
                        data_dict,
                        field,
                        name,
                        lambda check_box: (
                            check_box.checkState() ==
                            QtCore.Qt.CheckState.Checked
                        )
                    )
                )

            if type_ == 'textarea':
                field = textarea.TextAreaField(empty_text or '')
                if value is not None:
                    field.setPlainText(unicode(value))

                field.value_changed.connect(
                    functools.partial(
                        self.update_on_change,
                        data_dict,
                        field,
                        name,
                        lambda textarea_widget: textarea_widget.value()
                    )
                )

            if type_ == 'text':
                field = QtWidgets.QLineEdit()
                if value is not None:
                    field.insert(unicode(value))

                field.textChanged.connect(
                    functools.partial(
                        self.update_on_change,
                        data_dict,
                        field,
                        name,
                        lambda line_edit: line_edit.text()
                    )
                )

            if type_ == 'number':
                field = QtWidgets.QDoubleSpinBox()
                if value is not None:
                    field.setValue(float(value))

                field.setMaximum(sys.maxint)
                field.setMinimum(-sys.maxint)

                field.valueChanged.connect(
                    functools.partial(
                        self.update_on_change,
                        data_dict,
                        field,
                        name,
                        lambda spin_box: spin_box.value()
                    )
                )

            if type_ == 'enumerator':
                field = QtWidgets.QComboBox()
                for item in option['data']:
                    field.addItem(item['label'])

                field.currentIndexChanged.connect(
                    functools.partial(
                        self.update_on_change,
                        data_dict,
                        field,
                        name,
                        lambda box: (
                            option['data'][box.currentIndex()]['value']
                        )
                    )
                )

            if type_ == 'qt_widget':
                field = option['widget']
                field.value_changed.connect(
                    functools.partial(
                        self.update_on_change,
                        data_dict,
                        field,
                        name,
                        lambda custom_field: (
                            custom_field.value()
                        )
                    )
                )

            if field is not None:
                if label:
                    label_widget = QtWidgets.QLabel(label)
                    self.layout().addRow(label_widget, field)
                else:
                    self.layout().addRow(field)

    def update_on_change(
        self, data_dict, form_widget, name, value_provider, *args
    ):
        '''Update *instance* options from *form_widget*.'''
        value = value_provider(form_widget)
        data_dict[name] = value


class BaseSettingsProvider(object):
    '''Provides qt widgets to configure settings for a pyblish entity.'''

    def __init__(self):
        '''Instantiate provider with *pyblish_plugins*.'''
        super(BaseSettingsProvider, self).__init__()

    def __call__(self, label, options, store):
        '''Return a qt widget from *item*.'''
        tooltip = None

        if label is not None:
            settings_widget = QtWidgets.QGroupBox(label)
        else:
            settings_widget = QtWidgets.QWidget()

        settings_widget.setLayout(QtWidgets.QVBoxLayout())
        if tooltip:
            settings_widget.setToolTip(tooltip)

        if isinstance(options, QtWidgets.QWidget):
            settings_widget.layout().addWidget(options)
        else:
            settings_widget.layout().addWidget(
                ActionSettingsWidget(store, options)
            )

        return settings_widget


class Workflow(QtWidgets.QWidget):
    '''Publish dialog.'''

    OVERLAY_MESSAGE_TIMEOUT = 1

    def __init__(
        self, label, description, publish_asset, session,
        settings_provider=None, parent=None
    ):
        '''Display instances that can be published.'''
        super(Workflow, self).__init__()
        self.setObjectName('ftrack-workflow-widget')
        self.session = session
        self._label_text = label
        self.publish_asset = publish_asset

        plugin = ftrack_connect_pipeline.get_plugin()
        plugin_information = plugin.get_plugin_information()
        event_metadata = {
            'workflow_label': self._label_text,
        }
        if isinstance(plugin_information, dict):
            event_metadata.update(plugin_information)

        send_usage(
            'USED-FTRACK-CONNECT-PIPELINE-PUBLISH',
            event_metadata
        )

        self.publish_asset.prepare_publish()

        self.item_options_store = {}
        self.general_options_store = {}

        self.settings_provider = settings_provider
        if self.settings_provider is None:
            self.settings_provider = BaseSettingsProvider()

        self.settings_map = {}
        list_instances_widget = QtWidgets.QFrame()
        list_instances_widget.setObjectName('ftrack-instances-widget')

        self._list_instances_layout = QtWidgets.QVBoxLayout()

        list_instances_widget.setLayout(self._list_instances_layout)
        self._list_instances_layout.setContentsMargins(5, 5, 5, 5)

        list_instance_settings_widget = QtWidgets.QFrame()
        list_instance_settings_widget.setObjectName('ftrack-instances-settings-widget')

        self._list_items_settings_layout = QtWidgets.QVBoxLayout()
        self._list_items_settings_layout.addStretch(1)
        list_instance_settings_widget.setLayout(
            self._list_items_settings_layout
        )
        self._list_items_settings_layout.setContentsMargins(5, 5, 5, 5)

        configuration_layout = QtWidgets.QHBoxLayout()
        configuration_layout.addWidget(list_instances_widget, stretch=1)
        configuration_layout.addWidget(list_instance_settings_widget, stretch=1)
        configuration = QtWidgets.QFrame()
        configuration.setObjectName('ftrack-configuration-widget')
        configuration.setLayout(configuration_layout)
        configuration_layout.setContentsMargins(0, 0, 0, 0)

        information_layout = QtWidgets.QHBoxLayout()
        information_layout.addWidget(
            QtWidgets.QLabel('<h3>{0}</h3>'.format(self._label_text))
        )
        information_layout.addWidget(
            QtWidgets.QLabel('<i>{0}</i>'.format(description)),
            stretch=1
        )
        information = QtWidgets.QFrame()
        information.setObjectName('ftrack-information-widget')
        information.setLayout(information_layout)
        information_layout.setContentsMargins(0, 0, 0, 0)

        publish_button = QtWidgets.QPushButton('Publish')
        publish_button.clicked.connect(self.on_publish_clicked)

        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)
        self.layout().setContentsMargins(0, 0, 0, 0)

        scroll = QtWidgets.QScrollArea(self)

        scroll.setWidgetResizable(True)
        scroll.setLineWidth(0)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scroll.setWidget(configuration)

        self._list_instances_layout.addWidget(information)

        main_layout.addWidget(scroll, stretch=1)
        self._list_items_settings_layout.addWidget(publish_button)

        self._publish_overlay = BusyOverlay(
            self,
            message='Publishing Assets...'
        )
        self._publish_overlay.setStyleSheet(OVERLAY_DARK_STYLE)
        self._publish_overlay.setVisible(False)

        self.result_win = PublishResult(self.session, self)
        self.result_win.setStyleSheet(OVERLAY_DARK_STYLE)
        self.result_win.setVisible(False)

        self.refresh()

    def refresh(self):
        '''Refresh content.'''
        layout = self._list_instances_layout

        general_options = self.publish_asset.get_options()
        if general_options:
            settings_widget = self.settings_provider(
                label=None,
                options=general_options,
                store=self.general_options_store
            )
            self._list_items_settings_layout.insertWidget(0, settings_widget)

        items = self.publish_asset.get_publish_items()

        self.list_items_view = ListItemsWidget(items)
        self.list_items_view.itemChanged.connect(self.on_selection_changed)

        scene_select_button = QtWidgets.QPushButton('Scene selection')

        scene_select_button.clicked.connect(
            self._on_sync_scene_selection
        )
        layout.addWidget(scene_select_button)

        layout.addWidget(self.list_items_view, stretch=0)

        for item in items:
            if item.get('value') is True:
                self.add_instance_settings(item)

        self.list_items_view.setFocus()

    @ftrack_connect_pipeline.util.asynchronous
    def _hideOverlayAfterTimeout(self, timeout):
        '''Hide overlay after *timeout* seconds.'''
        time.sleep(timeout)
        self._publish_overlay.setVisible(False)

    def on_selection_changed(self, widget):
        '''Handle selection changed.'''
        item = widget.item()

        if widget.checkState() is QtCore.Qt.CheckState.Checked:
            self.add_instance_settings(item)
        else:
            self.remove_instance_settings(item)

    def add_instance_settings(self, item):
        '''Generate settings for *item*.'''
        save_options_to = self.item_options_store[item['name']] = dict()
        item_options = self.publish_asset.get_item_options(item['name'])
        if item_options:
            item_settings_widget = self.settings_provider(
                item['label'],
                item_options,
                save_options_to
            )
            self.settings_map[item['name']] = item_settings_widget
            self._list_items_settings_layout.addWidget(item_settings_widget)

    def remove_instance_settings(self, item):
        '''Remove *item*.'''
        try:
            item_settings_widget = self.settings_map.pop(item['name'])
        except KeyError:
            pass
        else:
            self._list_items_settings_layout.removeWidget(
                item_settings_widget
            )
            item_settings_widget.setParent(None)

    def on_publish_clicked(self):
        '''Handle publish clicked event.'''
        self._publish_overlay.setVisible(True)
        app = QtWidgets.QApplication.instance()
        app.processEvents()

        selected_item_names = []
        for item in self.list_items_view.get_checked_items():
            selected_item_names.append(item['name'])

        result = self.publish_asset.publish(
            self.item_options_store,
            self.general_options_store,
            selected_item_names
        )
        self._publish_overlay.setVisible(False)

        self._hideOverlayAfterTimeout(self.OVERLAY_MESSAGE_TIMEOUT)

        self.result_win.setVisible(True)
        self.result_win.populate(
            label=self._label_text,
            details_window_callback=getattr(
                self.publish_asset, 'show_detailed_result', None
            ),
            close_window_callback=self.on_close_callback,
            result=result
        )

    def on_close_callback(self):
        '''Handle close callback.'''
        self.result_win.setVisible(False)
        self.publish_asset.prepare_publish()

    def _on_sync_scene_selection(self):
        '''Handle sync scene selection event.'''
        scene_selection_names = set(self.publish_asset.get_scene_selection())
        self.list_items_view.update_selection(
            scene_selection_names
        )
