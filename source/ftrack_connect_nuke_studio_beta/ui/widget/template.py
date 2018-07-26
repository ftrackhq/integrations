import logging
import ftrack_connect.ui.widget.html_combobox
import ftrack_connect_nuke_studio_beta.template as template_manager

logger = logging.getLogger(__name__)


class Template(ftrack_connect.ui.widget.html_combobox.HtmlComboBox):
    '''Template combobox.'''

    def __init__(self, project, parent=None):
        '''Initialise template combobox.'''

        super(Template, self).__init__(
            self.format, parent=parent
        )

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.currentIndexChanged.connect(self.on_index_changed)
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
        self.currentIndexChanged.emit(default_index)

    def selected_template(self):
        '''Return currently selected template.'''
        return self.itemData(self.currentIndex())

    def format(self, data):
        '''Return data formatted as string.'''
        return u'<p><b>{0}</b><br>{1}</p>'.format(
            data.get('name'), data.get('description')
        )

    def on_index_changed(self, index):
        project = self.project
        template = self.selected_template()
        if template and project:
            template_manager.save_project_template(project, template)