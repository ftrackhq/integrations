# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import sys
import string
import functools
import time
import webbrowser

from QtExt import QtGui, QtCore, QtWidgets

from ftrack_api.event.base import Event

from ftrack_connect_pipeline.ui.widget.overlay import BusyOverlay
from ftrack_connect_pipeline.ui.widget.overlay import Overlay
from ftrack_connect_pipeline.ui.usage import send_event as send_usage
from ftrack_connect_pipeline.ui.style import OVERLAY_DARK_STYLE
import ftrack_connect_pipeline.util


class PublishResult(Overlay):
    '''Publish result overlay.'''

    def __init__(self, session, parent):
        '''Instantiate publish result overlay.'''
        super(PublishResult, self).__init__(parent=parent)
        self.session = session

    def populate(
        self, label, details_window_callback, result
    ):
        '''Populate with content.'''
        self.details_window_callback = details_window_callback

        self.asset_version = result['asset_version']
        success = result['success']

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        icon = QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor')
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

        if success:
            congrat_label = QtWidgets.QLabel('<h2>Publish Successful!</h2>')
            success_label = QtWidgets.QLabel(
                'Your <b>{0}</b> has been successfully published.'.format(
                    label
                )
            )
        else:
            congrat_label = QtWidgets.QLabel('<h2>Publish Failed!</h2>')
            success_label = QtWidgets.QLabel(
                'Your <b>{0}</b> failed to published. See details for more '
                'information.'.format(
                    label
                )
            )

        congrat_label.setAlignment(QtCore.Qt.AlignCenter)
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

        self.open_in_ftrack = QtWidgets.QPushButton('Open In Ftrack')
        buttons_layout.addWidget(self.open_in_ftrack)
        self.open_in_ftrack.clicked.connect(self.on_open_in_ftrack)

        if self.asset_version is None:
            self.open_in_ftrack.setDisabled(True)

    def on_show_details(self):
        '''Handle show of details.'''
        self.details_window_callback()

    def on_open_in_ftrack(self):
        '''Open result in ftrack.'''
        data = {
            'server_url': self.session.server_url,
            'version_id': self.asset_version['id'],
            'project_id': self.asset_version['asset']['parent']['project']['id']
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
                field = QtWidgets.QTextEdit()
                if value is not None:
                    field.setPlainText(unicode(value))

                field.textChanged.connect(
                    functools.partial(
                        self.update_on_change,
                        data_dict,
                        field,
                        name,
                        lambda text_area: text_area.toPlainText()
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

        result = self.session.event_hub.publish(
            Event(
                topic='ftrack.pipeline.get-plugin-information'
            ),
            synchronous=True
        )
        send_usage(
            'USED-FTRACK-CONNECT-PIPELINE-PUBLISH',
            {
                'asset_type': self._label_text,
                'plugin_information': result
            }
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
        list_instance_settings_widget.setObjectName('ftrack-instances-widget')

        self._list_items_settings_layout = QtWidgets.QVBoxLayout()
        self._list_items_settings_layout.addStretch(1)
        list_instance_settings_widget.setLayout(
            self._list_items_settings_layout
        )
        self._list_items_settings_layout.setContentsMargins(5, 5, 5, 5)

        configuration_layout = QtWidgets.QHBoxLayout()
        configuration_layout.addWidget(list_instances_widget, stretch=1)
        configuration_layout.addWidget(list_instance_settings_widget, stretch=1)
        configuration = QtWidgets.QWidget()
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
        information = QtWidgets.QWidget()
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

        toolbar = QtWidgets.QToolBar()
        action = toolbar.addAction('Scene selection')

        action.triggered.connect(
            self._on_sync_scene_selection
        )
        layout.addWidget(toolbar)

        layout.addWidget(self.list_items_view, stretch=0)

        for item in items:
            if item.get('value') is True:
                self.add_instance_settings(item)

        # layout.addStretch(1)

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
            result=result
        )

    def _on_sync_scene_selection(self):
        '''Handle sync scene selection event.'''
        scene_selection_names = set(self.publish_asset.get_scene_selection())
        self.list_items_view.update_selection(
            scene_selection_names
        )
