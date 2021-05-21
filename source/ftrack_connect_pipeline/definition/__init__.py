# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline.definition import collect, validate

logger = logging.getLogger(__name__)


def collect_and_validate(session, current_dir, host_type):
    '''
    Collects and validates the definitions and the schemas of the given *host*
    in the given *current_dir*.

    *session* : instance of :class:`ftrack_api.session.Session`
    *current_dir* : Directory path to look for the definitions.
    *host* : Definition host to look for.
    '''
    data = collect.collect_definitions(current_dir)

    # # filter definitions
    data = collect.filter_definitions_by_host(data, host_type)
    #
    # # validate schemas
    data = validate.validate_schema(data)
    #
    # # validate asset types
    data = validate.validate_asset_types(data, session)
    #
    # # validate packages
    data = validate.validate_package_type(data)
    #
    # # validate packages
    data = validate.validate_definition_components(data)

    # # resolve schemas

    data = collect.resolve_schemas(data)

    # log final discovery result
    for key, value in list(data.items()):
        logger.debug('discovered : {} : {}'.format(key, len(value)))


    return data
