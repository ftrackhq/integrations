# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.ui.factory import default as default_widgets
from ftrack_connect_pipeline_qt.ui.factory import overrides as override_widgets
from ftrack_connect_pipeline import constants as core_constants

''' Configures which widgets that factory should use when building the UI
based on a definition, for a given client type.'''
UI_OVERRIDES = {
    'progress_widget': default_widgets.ProgressWidgetObject,
    'progress_widget.loader': default_widgets.BatchProgressWidget,
    'main_widget': default_widgets.DefaultMainWidgetObject,
    core_constants.CONTEXTS: {
        'step_container': default_widgets.DefaultStepContainerWidgetObject,
        'step_widget': None,
        'stage_widget': default_widgets.DefaultStageWidgetObject,
        'plugin_container': None,
    },
    core_constants.COMPONENTS: {
        'step_container': default_widgets.DefaultStepContainerWidgetObject,
        'step_container.opener': override_widgets.RadioButtonStepContainerWidgetObject,
        'step_widget.opener': override_widgets.RadioButtonStepWidgetObject,
        'step_widget.loader': override_widgets.LoaderStepWidgetObject,
        'step_widget.publisher': override_widgets.PublisherAccordionStepWidgetObject,
        'stage_widget': default_widgets.DefaultStageWidgetObject,
        # Example to override specific stage widget
        # 'stage_widget.collector': default_widgets.DefaultStageWidgetObject,
        'plugin_container': default_widgets.DefaultPluginContainerWidgetObject,
        # We are saying that all the plugins of type validator will not have a plugin container
        'plugin_container.validator': None,
        'plugin_container.exporter': None,
        # Example to override specific plugin container
        # 'plugin_container.collect from given path': default_widgets.DefaultPluginContainerWidgetObject,
    },
    core_constants.FINALIZERS: {
        'show': True,
        'progress.label.publisher': 'to ftrack',
        'step_container': default_widgets.DefaultStepContainerWidgetObject,
        'step_widget': default_widgets.DefaultStepWidgetObject,
        'stage_widget': default_widgets.DefaultStageWidgetObject,
        'plugin_container': override_widgets.AccordionPluginContainerWidgetObject,
    },
}
