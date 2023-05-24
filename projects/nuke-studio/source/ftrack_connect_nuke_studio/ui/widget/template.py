# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging
import ftrack_connect_nuke_studio.ui.widget.html_combobox
import ftrack_connect_nuke_studio.template as template_manager

logger = logging.getLogger(__name__)


class Template(ftrack_connect_nuke_studio.ui.widget.html_combobox.HtmlComboBox):
    '''Template combobox.'''

    def __init__(self, project, parent=None):
        '''Initialise template combobox.'''

        super(Template, self).__init__(
            self.format, parent=parent
        )

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.currentIndexChanged.connect(self.index_changed)
        self.project = project
        self._templates = template_manager.available_templates(project)

        default_index = 0
        for index, template in enumerate(self._templates):
            self.addItem(template['name'])
            self.setItemData(
                index, template
            )

            if template.get('default'):
                default_index = index

        self.setCurrentIndex(default_index)
        # Somehow setCurrentIndex does not trigger currentIndexChanged so we do it.
        self.currentIndexChanged.emit(default_index)

    def selected_template(self):
        '''Return currently selected template.'''
        return self.itemData(self.currentIndex())

    def format(self, data):
        '''Return data formatted as string.'''
        return u'<p><b>{0}</b><br>{1}</p>'.format(
            data.get('name'), data.get('description')
        )

    def index_changed(self, index):
        project = self.project
        template = self.selected_template()
        if template and project:
            template_manager.save_project_template(project, template)