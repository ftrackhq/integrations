# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline_qt.client.documentation import QtDocumentationClientWidget
from {{cookiecutter.package_name}} import utils as {{cookiecutter.host_type}}_utils


class {{cookiecutter.host_type_capitalized}}QtDocumentationClientWidget(QtDocumentationClientWidget):
    '''{{cookiecutter.host_type_capitalized}} documentation client'''

    dcc_utils = {{cookiecutter.host_type}}_utils
