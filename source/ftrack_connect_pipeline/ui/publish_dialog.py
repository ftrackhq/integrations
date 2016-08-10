import collections
import string
import functools

import pyblish.util
import pyblish.api
import pyblish.logic

from PySide import QtGui, QtCore


class SelectableInstanceWidget(QtGui.QListWidgetItem):
    '''A selectable instance widget.'''

    def __init__(self, instance):
        '''Instanstiate widget from *instance*.'''
        super(SelectableInstanceWidget, self).__init__()
        self._pyblish_instance = instance
        self.setText(instance.name)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)

        self.setCheckState(
            QtCore.Qt.Checked
            if instance.data.get('publish') is True
            else QtCore.Qt.Unchecked
        )

    def pyblish_instance(self):
        '''Return pyblish instance.'''
        return self._pyblish_instance


class InstanceListWidget(QtGui.QListWidget):
    '''List of instances.'''

    def __init__(self, instances):
        '''Instanstiate and generate list from *instances*.'''
        super(InstanceListWidget, self).__init__()

        for instance in instances:
            item = SelectableInstanceWidget(instance)
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

    def __init__(self, pyblish_plugins):
        '''Instantiate provider with *pyblish_plugins*.'''
        super(BaseSettingsProvider, self).__init__()

        self.pyblish_plugins = pyblish_plugins
        self._compatible_context_plugins = []
        self._compatible_instance_plugins = []

        for plugin in self.pyblish_plugins:
            if plugin.order >= pyblish.api.ExtractorOrder:
                #: TODO: Change to better way to determine if it is a context
                # plugin.
                if plugin.__contextEnabled__:
                    self._compatible_context_plugins.append(plugin)
                else:
                    self._compatible_instance_plugins.append(plugin)

    def __call__(self, pyblish_entity):
        '''Return a qt widget from *pyblish_entity*.'''
        tooltip = None
        label = ''
        compatible_plugins = []

        if isinstance(pyblish_entity, pyblish.api.Context):
            compatible_plugins = self._compatible_context_plugins[:]
            label = 'Publish options'
            tooltip = (
                'These options will be saved in the Pyblish Context and used '
                'in validation, extraction and integration steps.'
            )

        elif isinstance(pyblish_entity, pyblish.api.Instance):
            for plugin in self._compatible_instance_plugins:
                if (
                    pyblish_entity.data['family'] in plugin.families
                ):
                    compatible_plugins.append(plugin)

            label = pyblish_entity.name
            tooltip = (
                'These options will be saved in the {0} Pyblish Instance and '
                'used in validation, extraction and integration steps.'.format(
                    pyblish_entity.name
                )
            )

        else:
            raise ValueError(
                'Must provide a valid pyblish instance or context. {0!r} is '
                'unknown.'.format(pyblish_entity)
            )

        settings_widget = QtGui.QGroupBox(label)
        settings_widget.setLayout(QtGui.QVBoxLayout())
        if tooltip:
            settings_widget.setToolTip(tooltip)

        for plugin in compatible_plugins:
            if hasattr(plugin, '_ftrack_options'):
                options = plugin._ftrack_options(pyblish_entity)

                if isinstance(options, QtGui.QWidget):
                    settings_widget.layout().addWidget(options)
                else:
                    settings_widget.layout().addWidget(
                        ActionSettingsWidget(pyblish_entity.data, options)
                    )

        return settings_widget


class PublishDialog(QtGui.QDialog):
    '''Publish dialog.'''

    def __init__(
        self, label, description, instance_filter, settings_provider=None,
        parent=None
    ):
        '''Display instances that can be published.'''
        super(PublishDialog, self).__init__()
        self.setMinimumSize(800, 600)

        self._pyblish_plugins = pyblish.api.discover()

        self.settings_provider = settings_provider
        if self.settings_provider is None:
            self.settings_provider = BaseSettingsProvider(self._pyblish_plugins)

        self.settings_map = {}
        self._pyblish_context = pyblish.api.Context()

        self.instance_filter = instance_filter

        list_instances_widget = QtGui.QWidget()
        self._list_instances_layout = QtGui.QVBoxLayout()
        list_instances_widget.setLayout(self._list_instances_layout)

        list_instance_settings_widget = QtGui.QWidget()
        self._list_instance_settings_layout = QtGui.QVBoxLayout()
        self._list_instance_settings_layout.addStretch(1)
        list_instance_settings_widget.setLayout(
            self._list_instance_settings_layout
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
        context = pyblish.util.collect(context=self._pyblish_context)

        settings_widget = self.settings_provider(context)
        self._list_instance_settings_layout.insertWidget(0, settings_widget)

        groups = collections.defaultdict(list)
        for instance in context:
            if self.instance_filter(instance):
                group_key = instance.data.get('family', 'other')
                groups[group_key].append(instance)

        for group_key, instances in groups.items():
            view = InstanceListWidget(instances)
            view.itemChanged.connect(self.on_selection_changed)
            layout.addWidget(
                QtGui.QLabel(
                    'Select {0}(s) to publish'.format(
                        string.capitalize(group_key)
                    )
                )
            )
            layout.addWidget(view, stretch=0)

            for instance in instances:
                if instance.data.get('publish') is True:
                    self.add_instance_settings(instance)

        layout.addStretch(1)

    def on_selection_changed(self, item):
        '''Handle selection changed.'''
        instance = item.pyblish_instance()

        if item.checkState() is QtCore.Qt.CheckState.Checked:
            instance.data['publish'] = True
            self.add_instance_settings(instance)
        else:
            instance.data['publish'] = False
            self.remove_instance_settings(instance)

    def add_instance_settings(self, instance):
        '''Generate settings for *instance*.'''
        instance_settings_widget = self.settings_provider(instance)
        self.settings_map[id(instance)] = instance_settings_widget
        self._list_instance_settings_layout.insertWidget(
            0, instance_settings_widget
        )

    def remove_instance_settings(self, instance):
        '''Remove *instance*.'''
        instance_settings_widget = self.settings_map.pop(id(instance))
        self._list_instance_settings_layout.removeWidget(
            instance_settings_widget
        )
        instance_settings_widget.setParent(None)

    def on_publish_clicked(self):
        '''Handle publish clicked event.'''
        assert self._pyblish_context is not None
        context = self._pyblish_context
        non_collector_plugins = [
            plugin for plugin in self._pyblish_plugins
            if plugin.order > pyblish.api.CollectorOrder
        ]

        pyblish.util.publish(context=context, plugins=non_collector_plugins)
