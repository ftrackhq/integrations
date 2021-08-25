from ftrack_connect_pipeline_qt.client.widgets.experimental import default as default_widgets
from ftrack_connect_pipeline_qt.client.widgets.experimental import overrides as override_widgets
from ftrack_connect_pipeline import constants as core_constants

UI_OVERRIDES = {
    'progress_widget': default_widgets.ProgressWidget,
    'main_widget': default_widgets.DefaultMainWidget,
    core_constants.CONTEXTS: {
        'step_container': default_widgets.DefaultStepContainerWidget,
        'step_widget': None,
        'stage_widget': default_widgets.DefaultStageWidget,
        'plugin_container': None
    },
    core_constants.COMPONENTS: {
        'step_container': default_widgets.DefaultStepContainerWidget,
        'step_widget': override_widgets.AccordionStepWidget,
        'stage_widget': default_widgets.DefaultStageWidget,
        # Example to override specific stage widget
        # 'stage_widget.collector': default_widgets.DefaultStageWidget,
        'plugin_container': None, # override_widgets.AccordionPluginContainerWidget,
        # Example to override specific plugin container
        # 'plugin_container.collect from given path': default_widgets.DefaultPluginContainerWidget,
    },
    core_constants.FINALIZERS: {
        'show': False,
        'step_container': override_widgets.TabStepContainerWidget,
        'step_widget': default_widgets.DefaultStepWidget,
        'stage_widget': override_widgets.GroupBoxStageWidget,
        'plugin_container': override_widgets.AccordionPluginContainerWidget,
    }
}