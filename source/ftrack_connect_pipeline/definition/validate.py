# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import copy
import json
import python_jsonschema_objects as pjo
import logging

logger = logging.getLogger(__name__)


def _validate_and_augment_schema(schema, definition ,type):
    '''Validate all the given definitions with the given schema'''
    builder = pjo.ObjectBuilder(schema)
    ns = builder.build_classes(standardize_names=False)
    ObjectBuilder = getattr(ns, type.capitalize())
    klass = ObjectBuilder(**definition)
    serialised_data = klass.serialize()
    return json.loads(serialised_data)


def validate_schema(data):
    copy_data = copy.deepcopy(data)
    # validate schema
    for schema in data['schema']:
        for entry in ['loader', 'publisher', 'package']:
            if schema['title'].lower() == entry:
                for definition in data[entry]:
                    augumented_valid_data = None
                    try:
                        augumented_valid_data = _validate_and_augment_schema(
                            schema, definition, entry
                        )
                    except Exception as error:
                        logger.warning(
                            'definitinon {} does not match any schema. {}'.format(
                                definition['name'], str(error)
                            )
                        )
                        copy_data[entry].remove(definition)
                        continue

                    copy_data[entry].remove(definition)
                    copy_data[entry].append(augumented_valid_data)

    return copy_data


def validate_asset_types(data, session):
    # validate package asset types:
    copy_data = copy.deepcopy(data)
    valid_assets_types = [
        type['short'] for type in session.query('AssetType').all()
    ]

    for package in data['package']:
        if package['asset_type'] not in valid_assets_types:
            logger.warning(
                'Package {} does use a non existing'
                ' asset type: {}'.format(
                    package['name'], package['asset_type']
                    )
            )
            copy_data['package'].remove(package)

    return copy_data


def validate_package_type(data):
    # validate package
    copy_data = copy.deepcopy(data)
    valid_packages = [str(package['name']) for package in data['package']]
    for entry in ['loader', 'publisher']:

        # check package name in definitions
        for definition in data[entry]:
            if str(definition.get('package')) not in valid_packages:
                logger.warning(
                    '{} {}:{} use unknown package : {} , packages: {}'.format(
                        entry, definition['host'], definition['name'],
                        definition.get('package'), valid_packages)
                    )
                # pop definition
                copy_data[entry].remove(definition)

    return copy_data


def validate_definition_components(data):
    copy_data = copy.deepcopy(data)
    # validate package vs definitions components
    for package in data['package']:
        package_component_names = [
            component['name'] for component in package['components']
            if not component.get('optional', False)
        ]
        for entry in ['loader', 'publisher']:
            for definition in data[entry]:
                if definition['package'] != package['name']:
                    # this is not the package you are looking for....
                    continue

                definition_components_names = [
                    component['name'] for component in definition['components']
                ]

                for name in package_component_names:
                    if name not in definition_components_names:
                        logger.warning(
                            '{} {}:{} package {} components'
                            ' are not matching : required component: {}'.format(
                                entry, definition['host'], definition['name'],
                                definition['package'], package_component_names)
                        )
                        copy_data[entry].remove(definition)
                        break

    # reverse lookup for definitions components in packages
    for entry in ['loader', 'publisher']:
        for definition in copy_data[entry]:
            definition_components_names = [
                component['name'] for component in definition['components']
            ]
            for package in data['package']:
                if definition['package'] != package['name']:
                    # this is not the package you are looking for....
                    continue

                package_component_names = [
                    component['name'] for component in package['components']
                ]

                component_diff = set(
                    definition_components_names
                ).difference(
                    set(package_component_names)
                )
                if len(component_diff) != 0:
                    logger.warning(
                        '{} {}:{} package {} components'
                        ' are not matching : required component: {}'.format(
                            entry, definition['host'], definition['name'],
                            definition['package'], package_component_names)
                    )
                    copy_data[entry].remove(definition)

    return copy_data