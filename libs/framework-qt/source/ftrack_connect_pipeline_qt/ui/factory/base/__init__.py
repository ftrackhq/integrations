# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging
import uuid

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline_qt.ui.utility.widget import line


class BaseUIWidgetObject(object):
    '''
    Base class of a widget representation from json schema types, wrapping a QT widget.
    Instantiated from the widget factory.
    '''

    @property
    def name(self):
        '''Return the name of the widget'''
        return self._name

    @name.setter
    def name(self, value):
        '''Sets the name of widget to *value*'''
        self._name = value

    @property
    def widget_id(self):
        '''Return the widget unique id'''
        return self._widget_id

    @property
    def widget(self):
        '''Return the actual wrapped QT widget'''
        return self._widget

    @property
    def enabled(self):
        '''Return True if widget is enabled as evaluated from schema'''
        return self._is_enabled

    @enabled.setter
    def enabled(self, value):
        '''Set widget enable property'''
        self._is_enabled = value

    @property
    def optional(self):
        '''Return True if widget is optional or not as evaluated from schema'''
        return self._is_optional

    def __init__(self, name, fragment_data, parent=None):
        '''
        Initialise BaseUIWidgetObject

        :param name: The name of the widget as evaluated from schema
        :param fragment_data: JSON fragment of the data from the definition to fill the current widget.
        :param parent: the parent dialog or frame
        '''
        super(BaseUIWidgetObject, self).__init__()
        # setup default vars
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.fragment_data = fragment_data
        self._parent = parent

        self.name = name
        self._widget = None
        self._widget_id = uuid.uuid4().hex
        self._is_optional = False
        self._is_enabled = True
        self.description = None
        if self.fragment_data:
            self.description = self.fragment_data.get(
                'description', 'No description provided'
            )
            self._is_optional = self.fragment_data.get('optional', False)
            self._is_enabled = self.fragment_data.get('enabled', True)
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Pre-build function, mostly used to setup the widget's layout. To be overridden by child'''
        pass

    def build(self):
        '''Build function, mostly used to create the widgets. To be overridden by child'''
        pass

    def post_build(self):
        '''post build function , mostly used connect widgets events. To be overridden by child'''
        if self.widget and self.widget.layout():
            self.widget.layout().setContentsMargins(0, 0, 0, 0)
            self.widget.layout().setSpacing(5)
            self.widget.setToolTip(self.description)

    def parent(self):
        '''Return the parent widget'''
        return self._parent

    def parent_widget(self, widget, add_line=False):
        '''Add the *widget* to wrapped widget layout, setting this widget (me) to be the parent.'''
        if self.widget:
            widget = (
                widget.widget
                if isinstance(widget, BaseUIWidgetObject)
                else widget
            )
            self.widget.layout().addWidget(widget)
            if add_line:
                self.widget.layout().addWidget(line.Line())
            if (
                self.fragment_data
                and self.fragment_data.get('visible', True) is False
            ):
                self._widget.setVisible(False)
        else:
            self.logger.error("Please create a widget before parent")

    def parent_validator(self, step_widget):
        '''Parent the *step_widget* as validator options. To be overridden by child'''
        raise NotImplementedError

    def parent_exporter(self, step_widget):
        '''Parent the *step_widget* as exporter options. To be overridden by child'''
        raise NotImplementedError

    def to_json_object(self):
        '''Return a formatted json with the data from the current widget'''
        return {}
