# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import hiero.core

import lucidity
import lucidity.error

import ftrack_api

import ftrack_connect_nuke_studio.exception

from ftrack_connect.session import (
    get_shared_session
)

session = get_shared_session()

def available_templates(project):
    '''Return available templates for *project*.

    If a template has been saved on the project using
    :meth:`save_project_template` that template will contain a `default` key
    set to True.

    '''
    templates = []
    responses = session.event_hub.publish(
        ftrack_api.event.base.Event(
            topic='ftrack.connect.nuke-studio.get-context-templates'
        ),
        synchronous=True
    )

    for response in responses:
        templates += response

    project_template = get_project_template(project)

    if project_template:
        for template in templates:
            if template['name'] == project_template['name']:
                template['default'] = True
                break
        else:
            templates.append(project_template)

    return templates


def get_project_template(project):
    '''Return template stored on *project*.'''
    template = None
    # Fetch the templates from tags on sequences on the project.
    # This is a workaround due to that projects do not have tags or metadata.
    for sequence in project.sequences():
        for tag in sequence.tags():
            if tag.name() == 'ftrack.template':
                template = {
                    'name': tag.metadata().value('ftrack.template.name'),
                    'description': tag.metadata().value(
                        'ftrack.template.description'
                    ),
                    'expression': tag.metadata().value(
                        'ftrack.template.expression'
                    ),
                    'default': True
                }
                break

        if template:
            break

    return template


def save_project_template(project, template):
    '''Store *template* on *project*.'''

    # Store the template in a tag on all sequences on the project.
    # This is a workaround due to that projects do not have tags or metadata.
    for sequence in project.sequences():
        for _tag in sequence.tags()[:]:
            if _tag.name() == 'ftrack.template':
                sequence.removeTag(_tag)

        tag = hiero.core.Tag('ftrack.template')

        tag.metadata().setValue('ftrack.template.name', template['name'])
        tag.metadata().setValue(
            'ftrack.template.description', template['description']
        )
        tag.metadata().setValue(
            'ftrack.template.expression', template['expression']
        )
        tag.setVisible(False)

        sequence.addTag(tag)


def match(item, template):
    '''Return list of entites based on name of *clip* and *template*.'''
    expression = template['expression']
    lucidity_template = lucidity.template.Template(
        template['name'], expression, anchor=None
    )

    item_name = item.name()
    try:
        objects = lucidity_template.parse(item_name)
    except lucidity.error.ParseError:
        raise ftrack_connect_nuke_studio.exception.TemplateError(
            message=(
                '"{item_name}" did not match the '
                'template "{template_name}"'.format(
                    item_name=item_name, template_name=template['name']
                )
            )
        )

    hierarchy = []
    for object_type, object_name in objects.items():

        # Skip special `_` group used to remove things from name.
        if object_type == '_':
            continue

        # TODO: Validate that object type exist in ftrack. If not should
        # be marked as error.
        hierarchy.append(dict(
            object_type=object_type, name=object_name
        ))

    hierarchy = sorted(
        hierarchy, key=lambda x: expression.index(x['object_type'])
    )

    session.event_hub.publish(
        ftrack_api.event.base.Event(
            topic='ftrack.connect.nuke-studio.after-template-match',
            data={
                'application_object': item,
                'template': template,
                'structure': hierarchy
            }
        ),
        synchronous=True
    )

    return hierarchy
