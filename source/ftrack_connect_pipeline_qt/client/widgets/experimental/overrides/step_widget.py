from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client.widgets.experimental import BaseUIWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget

class AccordionStepWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    @property
    def is_enabled(self):
        if self._widget:
            return self._widget.is_checked()
        else:
            return self._is_enabled

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(AccordionStepWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def pre_build(self):
        self._is_optional = self.fragment_data.get('optional')

    def build(self):
        self._widget = AccordionWidget(
            title=self.name, checkable=self.is_optional
        )

    def parent_widget(self, step_widget):
        if self.widget:
            if hasattr(step_widget, 'widget'):
                self.widget.add_widget(step_widget.widget)
            else:
                self.widget.add_widget(step_widget)
        else:
            self.logger.error("Please create a widget before parent")

    def to_json_object(self):
        '''Return a formated json with the data from the current widget'''
        out = {}
        out['enabled'] = self.is_enabled
        return out