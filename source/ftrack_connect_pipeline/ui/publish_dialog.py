import string
import functools

from PySide import QtGui, QtCore


class SelectableItemWidget(QtGui.QListWidgetItem):
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


class ListItemsWidget(QtGui.QListWidget):
    '''List of items that can be published.'''

    def __init__(self, items):
        '''Instanstiate and generate list from *items*.'''
        super(ListItemsWidget, self).__init__()

        for item in items:
            item = SelectableItemWidget(item)
            self.addItem(item)


class ActionSettingsWidget(QtGui.QWidget):
    '''A widget to display settings.'''

    def __init__(self, data_dict, options):
        '''Instanstiate settings from *options*.'''
        super(ActionSettingsWidget, self).__init__()

        self.setLayout(QtGui.QFormLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        for option in options:
            type_ = option['type']
            label = option['label']
            name = option['name']
            value = option.get('value')
            if name in data_dict.get('options', {}):
                value = data_dict['options'][name]

            field = None

            if type_ == 'boolean':
                field = QtGui.QCheckBox()
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

            if type_ in ('number', 'text'):
                field = QtGui.QLineEdit()
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

            if type_ == 'enumerator':
                field = QtGui.QComboBox()
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

            if field is not None:
                label_widget = QtGui.QLabel(label)
                self.layout().addRow(
                    label_widget,
                    field
                )

    def update_on_change(
        self, data_dict, form_widget, name, value_provider, *args
    ):
        '''Update *instance* options from *form_widget*.'''
        value = value_provider(form_widget)
        if 'options' not in data_dict:
            data_dict['options'] = {}

        data_dict['options'][name] = value


class BaseSettingsProvider(object):
    '''Provides qt widgets to configure settings for a pyblish entity.'''

    def __init__(self):
        '''Instantiate provider with *pyblish_plugins*.'''
        super(BaseSettingsProvider, self).__init__()

    def __call__(self, label, options):
        '''Return a qt widget from *item*.'''
        tooltip = None
        settings_widget = QtGui.QGroupBox(label)
        settings_widget.setLayout(QtGui.QVBoxLayout())
        if tooltip:
            settings_widget.setToolTip(tooltip)

        if isinstance(options, QtGui.QWidget):
            settings_widget.layout().addWidget(options)
        else:
            settings_widget.layout().addWidget(
                ActionSettingsWidget(dict(), options)
            )

        return settings_widget


class PublishDialog(QtGui.QDialog):
    '''Publish dialog.'''

    def __init__(
        self, label, description, publish_asset, settings_provider=None,
        parent=None
    ):
        '''Display instances that can be published.'''
        super(PublishDialog, self).__init__()
        self.setMinimumSize(800, 600)

        self.publish_asset = publish_asset
        self.publish_data = self.publish_asset.prepare_publish()

        self.settings_provider = settings_provider
        if self.settings_provider is None:
            self.settings_provider = BaseSettingsProvider()

        self.settings_map = {}
        list_instances_widget = QtGui.QWidget()
        self._list_instances_layout = QtGui.QVBoxLayout()
        list_instances_widget.setLayout(self._list_instances_layout)

        list_instance_settings_widget = QtGui.QWidget()
        self._list_items_settings_layout = QtGui.QVBoxLayout()
        self._list_items_settings_layout.addStretch(1)
        list_instance_settings_widget.setLayout(
            self._list_items_settings_layout
        )

        configuration_layout = QtGui.QHBoxLayout()
        configuration_layout.addWidget(list_instances_widget, stretch=1)
        configuration_layout.addWidget(list_instance_settings_widget, stretch=1)
        configuration = QtGui.QWidget()
        configuration.setLayout(configuration_layout)

        information_layout = QtGui.QHBoxLayout()
        information_layout.addWidget(QtGui.QLabel('<h3>{0}</h3>'.format(label)))
        information_layout.addWidget(
            QtGui.QLabel('<i>{0}</i>'.format(description)),
            stretch=1
        )
        information = QtGui.QWidget()
        information.setLayout(information_layout)

        publish_button = QtGui.QPushButton('Publish')
        publish_button.clicked.connect(self.on_publish_clicked)

        main_layout = QtGui.QVBoxLayout(self)
        self.setLayout(main_layout)

        scroll = QtGui.QScrollArea(self)

        scroll.setWidgetResizable(True)
        scroll.setLineWidth(0)
        scroll.setFrameShape(QtGui.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scroll.setWidget(configuration)

        main_layout.addWidget(information)
        main_layout.addWidget(scroll, stretch=1)
        main_layout.addWidget(publish_button)

        self.refresh()

    def refresh(self):
        '''Refresh content.'''
        layout = self._list_instances_layout
        settings_widget = self.settings_provider(
            'General',
            self.publish_asset.get_options(self.publish_data)
        )
        self._list_items_settings_layout.insertWidget(0, settings_widget)

        items = self.publish_asset.get_publish_items(self.publish_data)

        view = ListItemsWidget(items)
        view.itemChanged.connect(self.on_selection_changed)
        layout.addWidget(
            QtGui.QLabel(
                'Select {0}(s) to publish'.format(
                    string.capitalize(self.publish_asset.label)
                )
            )
        )
        layout.addWidget(view, stretch=0)

        for item in items:
            if item.get('value') is True:
                self.add_instance_settings(item)

        layout.addStretch(1)

    def on_selection_changed(self, widget):
        '''Handle selection changed.'''
        item = widget.item()

        if widget.checkState() is QtCore.Qt.CheckState.Checked:
            self.add_instance_settings(item)
        else:
            self.remove_instance_settings(item)

    def add_instance_settings(self, item):
        '''Generate settings for *item*.'''
        item_settings_widget = self.settings_provider(
            item['label'],
            self.publish_asset.get_item_options(self.publish_data, item['name'])
        )
        self.settings_map[item['name']] = item_settings_widget
        self._list_items_settings_layout.insertWidget(
            0, item_settings_widget
        )

    def remove_instance_settings(self, item):
        '''Remove *item*.'''
        item_settings_widget = self.settings_map.pop(item['name'])
        self._list_items_settings_layout.removeWidget(
            item_settings_widget
        )
        item_settings_widget.setParent(None)

    def on_publish_clicked(self):
        '''Handle publish clicked event.'''
        self.publish_asset.publish(self.publish_data)
