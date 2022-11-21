# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
import logging
from ftrack_connect_pipeline.definition import collect, validate

logger = logging.getLogger(__name__)


def collect_and_validate(session, current_dir, host_types):
    '''
    Collects and validates the definitions and the schemas of the given *host*
    in the given *current_dir*.

    *session* : instance of :class:`ftrack_api.session.Session`
    *current_dir* : Directory path to look for the definitions.
    *host* : Definition host to look for.
    '''
    start = time.time()
    data = collect.collect_definitions(current_dir)

    # # filter definitions
    data = collect.filter_definitions_by_host(data, host_types)
    #
    # # validate schemas
    data = validate.validate_schema(data, session)
    #
    # # resolve schemas

    data = collect.resolve_schemas(data)
    end = time.time()
    logger.info('Discovery run in: {}s'.format(end - start))

    # log final discovery result
    for key, value in list(data.items()):
        logger.debug(
            'Discovering definition took : {} : {}'.format(key, len(value))
        )

    return data
