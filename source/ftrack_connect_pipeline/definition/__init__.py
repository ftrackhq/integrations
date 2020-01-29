import logging
from ftrack_connect_pipeline.definition import collect, validate

logger = logging.getLogger(__name__)


def collect_and_validate(session, current_dir, host):
    data = collect.collect_definitions(current_dir)

    # # filter definitions
    data = collect.filter_definitions_by_host(data, host)
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
    for key, value in data.items():
        logger.info('discovered : {} : {}'.format(key, len(value)))


    return data
