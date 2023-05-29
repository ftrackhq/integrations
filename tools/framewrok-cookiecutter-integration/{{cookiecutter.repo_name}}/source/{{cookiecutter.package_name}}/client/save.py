# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline_qt.client.save import QtSaveClientWidget
from {{cookiecutter.package_name}} import utils as {{cookiecutter.host_type}}_utils


class {{cookiecutter.host_type_capitalized}}QtSaveClientWidget(QtSaveClientWidget):
    '''Client for doing an incremental save of {{cookiecutter.host_type_capitalized}} scene locally

    This is sample code that exists here for reference and not used by the current
    version of the framework.
    '''

    dcc_utils = {{cookiecutter.host_type}}_utils
