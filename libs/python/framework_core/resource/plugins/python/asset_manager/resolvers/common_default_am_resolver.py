# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import re
import sys

import ftrack_api
from ftrack_connect_pipeline import plugin


class CommonDefaultAssetManagerResolverPlugin(
    plugin.AssetManagerResolvePlugin
):
    plugin_name = 'common_default_am_resolver'

    # Resolver config, loaded from options
    max_link_depth = 1  # Maximum number of links to traverse
    linked_only = True  # Only follow links, do not resolve parents (workflow) dependencies

    def get_linked_entities_recursive(
        self,
        entity,
        result,
        processed_entities,
        calling_entity=None,
        is_link=False,
        link_depth=0,
    ):
        '''Add *entity* to *result* if it has assets property that can be resolved or directly linked. Follow
        links/go to upstream parent to recursively add further related contexts, up to
        a *link_depth* of maximum 1 (default). Prevents cycles by adding *entity* to *processed_entities*.'''
        if entity is None:
            self.logger.debug(
                'Not resolving dependencies for {}({}) - null entity!'.format(
                    entity['name'] if entity else 'None',
                    entity['id'] if entity else 'None',
                )
            )
            return
        if calling_entity is not None:
            calling_entity_id = calling_entity['id']
        else:
            calling_entity_id = ''
        for (entity_id, processed_calling_entity_id) in processed_entities:
            if (
                entity_id == entity['id']
                and processed_calling_entity_id == calling_entity_id
            ):
                self.logger.debug(
                    '(Linked contexts) Not resolving dependencies for {}({}) - already processed from other entity({})!'.format(
                        entity['name'] if entity else 'None',
                        entity_id,
                        calling_entity_id,
                    )
                )
                return
        # Prevent infinite cycles - on called from the same entity
        processed_entities.append((entity['id'], calling_entity_id))

        # Find out entity type
        next_entity_type = context = asset = version_nr = None
        add_entity = False
        if entity.entity_type == 'AssetVersion':
            context = entity['task']
            asset = entity['asset']
            version_nr = entity['version']
            if is_link:
                add_entity = True
            else:
                next_entity_type = 'task'
        elif entity.entity_type == 'Asset':
            context = entity['parent']
            asset = entity
            next_entity_type = 'parent'
        elif entity.entity_type == 'Task':
            context = entity
            if is_link:
                add_entity = True
            elif 'parent' in entity and entity['parent'] is not None:
                next_entity_type = 'parent'
        else:
            if 'parent' in entity and entity['parent'] is not None:
                context = entity
                if is_link:
                    add_entity = True
                else:
                    next_entity_type = 'parent'
            elif 'project' in entity and entity['parent'] is not None:
                context = entity
                if is_link:
                    add_entity = True
                else:
                    next_entity_type = 'project'
        if context:
            link = [ctx['name'] for ctx in context['link']]
        else:
            link = [
                entity.get('full_name') or entity.get('name') or entity['id']
            ]
        if asset:
            link.append(asset['name'])
        if version_nr:
            link.append('v{}'.format(version_nr))
        indent = ' ' * 3 * len(link)  # Make logs easy to read

        self.logger.debug(
            '(Linked contexts) {}Processing: {}({})'.format(
                indent, '/'.join(link), entity['id']
            )
        )
        if not add_entity:
            # Resolve assets on context if
            if 'assets' in entity and self.linked_only is False:
                add_entity = True
        if add_entity:
            # Can only add context that has assets
            has_duplicate = False
            for existing_entity in result:
                if existing_entity['id'] == entity['id']:
                    self.logger.debug(
                        '(Linked contexts) {}NOT considering for resolve - already present'.format(
                            indent
                        )
                    )
                    has_duplicate = True
                    break
            if not has_duplicate:
                self.logger.debug(
                    '(Linked contexts) {}Considering for resolve'.format(
                        indent
                    )
                )
                result.append(entity)

        # Any explicit links? Make sure to fetch updated data from backend
        if 'incoming_links' in entity:
            have_links = False
            self.session.populate(entity, 'incoming_links')
            if entity['incoming_links'] is not None:
                for entity_link in entity.get('incoming_links'):
                    if entity_link['from_id'] == entity['id']:
                        continue  # Ignore link to itself
                    have_links = True
                    if link_depth < self.max_link_depth:
                        self.logger.debug(
                            '(Linked contexts) {}[{}]Traveling via incoming link from: {} {}({})'.format(
                                indent,
                                entity['name'],
                                entity_link['from'].entity_type,
                                entity_link['from']['name'],
                                entity_link['from_id'],
                            )
                        )
                        self.get_linked_entities_recursive(
                            entity_link['from'],
                            result,
                            processed_entities,
                            calling_entity=entity,
                            is_link=True,
                            link_depth=link_depth + 1,
                        )
                    else:
                        self.logger.debug(
                            '(Linked contexts) {}[{}]NOT Traveling via incoming link from: {} {}[{}], max link depth of {} encountered'.format(
                                indent,
                                entity['name'],
                                entity_link['from'].entity_type,
                                entity_link['from']['name'],
                                entity_link['from_id'],
                                link_depth,
                            )
                        )
            if (
                self.linked_only is True
                and have_links
                and entity.entity_type == 'Task'
            ):
                # The resolved context have explicit links, stop harvest dependencies within its parents
                self.logger.debug(
                    '(Linked contexts) {}[{}]Context has incoming links, not resolving further parent contexts'.format(
                        indent, entity['name']
                    )
                )
                next_entity_type = None
        if (
            next_entity_type is not None
            and self.linked_only is True
            and self.max_link_depth <= link_depth
        ):
            self.logger.debug(
                '(Linked contexts) {}[{}]Not resolving further parent contexts, max link depth of {} encountered'.format(
                    indent, entity['name'], link_depth
                )
            )
            next_entity_type = None
        if next_entity_type is not None:
            # Go upstream, even if we only resolve linked assets we need to follow
            self.logger.debug(
                '(Linked contexts) {}[{}]Traveling to: {}'.format(
                    indent, entity['name'], next_entity_type
                )
            )
            self.session.populate(entity, next_entity_type)
            self.get_linked_entities_recursive(
                entity[next_entity_type],
                result,
                processed_entities,
                calling_entity=entity,
                link_depth=link_depth,
            )

    def str_version(self, context, asset_version):
        '''Generate a human readable string representation of *asset_version* beneath *context*'''
        return '%s_%s_v%03d' % (
            context['name'],
            asset_version['asset']['name'],
            asset_version['version'],
        )

    def resolve_dependencies(self, entities, options):
        '''Generic dependency resolve, locates latest versions from *entities*,
        based on task type resolvable asset types supplied *options* and filters.'''
        self.logger.debug(
            'Resolving asset dependencies on {} context(s)'.format(
                len(entities)
            )
        )
        versions = []
        if len(options.get('asset_types', [])) == 0:
            self.logger.debug('No asset type rules in options!')
            return versions
        for entity in entities:
            self.logger.debug(
                '(Assets) Resolving entity {}[{}]'.format(
                    entity['name'], entity['id']
                )
            )
            add_version = False
            if entity.entity_type == 'AssetVersion':
                # Add this version
                asset_version = entity
                context = asset_version['asset']['parent']
                self.conditional_add_version(context, versions, asset_version)
            else:
                task = None
                assets = None
                if entity.entity_type == 'Task':
                    task = entity
                    context = task['parent']
                else:
                    context = entity
                self.session.populate(context, 'assets')
                have_matching_asset = False
                for asset in context.get('assets'):
                    asset_type_matches = False
                    for asset_type_option in options['asset_types']:
                        if (
                            asset_type_option['asset_type'] == '*'
                            or asset['type']['name'].lower()
                            == asset_type_option['asset_type'].lower()
                            or asset['type']['short'].lower()
                            == asset_type_option['asset_type'].lower()
                        ):
                            have_matching_asset = True
                            asset_type_matches = True
                            break

                    if asset_type_matches:
                        self.conditional_add_latest_version(
                            versions, context, task, asset, asset_type_option
                        )
                if not have_matching_asset:
                    self.logger.debug(
                        '(Assets)    [{}]No matching assets found, supported types:{}'.format(
                            context['name'], options['asset_types']
                        )
                    )

        return versions

    def conditional_add_latest_version(
        self, versions, context, task, asset, asset_type_option
    ):
        '''Filter context *ctx* and *asset* against *asset_type_option*, if they pass,
        add latest version to *versions*'''
        # We have a matching asset type, find latest version
        no_status_include_constraints = len(
            self._status_names_include or []
        ) == 0 or (
            len(self._status_names_include) == 1
            and self._status_names_include[0] == '.*'
        )
        no_status_exclude_constraints = len(
            self._status_names_exclude or []
        ) == 0 or (
            len(self._status_names_exclude) == 1
            and self._status_names_exclude[0] == '.^'
        )
        latest_version = None
        self.session.populate(asset, 'versions')
        task_projection = (
            (' and task.id={}'.format(task['id'])) if task else ''
        )
        if no_status_include_constraints and no_status_exclude_constraints:
            # No version status constraints
            latest_version = self.session.query(
                'AssetVersion where asset.id={}{} and is_latest_version is true'.format(
                    asset['id'], task_projection
                )
            ).first()
        elif (
            no_status_include_constraints
            and len(self._status_names_exclude) == 1
            and self._status_names_exclude[0] == '^Omitted$'
        ):
            # Framework default, treat this special to save performance
            latest_version = self.session.query(
                'AssetVersion where asset.id={}{} and status.name != "Omitted" '
                'order by version desc'.format(asset['id'], task_projection)
            ).first()
        else:
            # Find latest version by iterating versions and check statuses
            for version in self.session.query(
                'AssetVersion where asset.id={}{} '
                'order by version desc'.format(asset['id'], task_projection)
            ):
                # Check so it's not the calling context
                if version['task']['id'] == self._context['id']:
                    self.logger.debug(
                        '(Version)    Not considering version {} - beneath same context: {}.'.format(
                            self.str_version(context, version),
                            self._context['name'],
                        )
                    )
                    continue
                if len(self._status_names_include or []) > 0:
                    include = False
                    for status_name_include in self._status_names_include:
                        if re.match(
                            status_name_include, version['status']['name']
                        ):
                            include = True
                            break
                    if not include:
                        self.logger.debug(
                            '(Version)    Not considering version {} - does not include status(es): {}.'.format(
                                self.str_version(context, version),
                                self._status_names_include,
                            )
                        )
                        continue
                if len(self._status_names_exclude or []) > 0:
                    exclude = False
                    for status_name_exclude in self._status_names_exclude:
                        if re.match(
                            status_name_exclude, version['status']['name']
                        ):
                            exclude = True
                            break
                    if exclude:
                        self.logger.debug(
                            '(Version)    Not considering version {} - matches exclude status(es): {}.'.format(
                                self.str_version(context, version),
                                status_name_exclude,
                            )
                        )
                        continue
                latest_version = version
                break

        if latest_version:
            self.logger.debug(
                '(Version)    Got latest version {}, filtering and adding.'.format(
                    self.str_version(context, latest_version)
                )
            )
            if 'task_names_include' in asset_type_option.get('filters', {}):
                matches_all = True
                for expression in asset_type_option['filters'][
                    'task_names_include'
                ]:
                    if not re.match(expression, context['name'].lower()):
                        matches_all = False
                        break
                if not matches_all:
                    self.logger.debug(
                        '(Version)       Task name include filter mismatch: {} '.format(
                            context['name']
                        )
                    )
                    return
            if 'task_names_exclude' in asset_type_option.get('filters', {}):
                matches_any = False
                for expression in asset_type_option['filters'][
                    'task_names_exclude'
                ]:
                    if re.match(expression, context['name'].lower()):
                        matches_any = True
                        break
                if matches_any:
                    self.logger.debug(
                        '(Version)       Task name exclude filter mismatch: {} '.format(
                            context['name']
                        )
                    )
                    return
            if 'asset_names_include' in asset_type_option.get('filters', {}):
                matches_all = True
                for expression in asset_type_option['filters'][
                    'asset_names_include'
                ]:
                    if not re.match(expression, asset['name'].lower()):
                        matches_all = False
                        break
                if not matches_all:
                    self.logger.debug(
                        '(Version)       Asset name include filter mismatch: {} '.format(
                            asset['name']
                        )
                    )
                    return
            if 'asset_names_exclude' in asset_type_option.get('filters', {}):
                matches_any = False
                for expression in asset_type_option['filters'][
                    'asset_names_exclude'
                ]:
                    if re.match(expression, asset['name'].lower()):
                        matches_any = True
                        break
                if matches_any:
                    self.logger.debug(
                        '(Version)       Asset name exclude filter mismatch: {} '.format(
                            asset['name']
                        )
                    )
                    return
            # Check so it's not already in there
            self.conditional_add_version(context, versions, latest_version)
        else:
            self.logger.debug(
                '(Version)    No latest version on asset {}_{}.'.format(
                    context['name'], asset['name']
                )
            )

    def conditional_add_version(self, context, versions, asset_version):
        has_duplicate = False
        for version_data in versions:
            if version_data['entity']['id'] == asset_version['id']:
                has_duplicate = True
                break
        if not has_duplicate:
            # Add a dictionary, allowing further metadata to be passed with resolve at
            # a later stage
            self.logger.debug(
                '(Version)       Resolved: {}({}) '.format(
                    self.str_version(context, asset_version),
                    asset_version['id'],
                )
            )
            versions.append({'entity': asset_version})
        else:
            self.logger.debug(
                '(Version)       Version already resolved: {} '.format(
                    self.str_version(context, asset_version)
                )
            )

    # Task type specific resolvers

    def resolve_texture_dependencies(self, entities, options):
        '''Find latest texture dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further texture specific resolves/checks on result here
        return versions

    def resolve_vehicle_dependencies(self, entities, options):
        '''Find latest vehicle dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further vehicle specific resolves/checks on result here
        return versions

    def resolve_conform_dependencies(self, entities, options):
        '''Find latest conform dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further conform specific resolves/checks on result here
        return versions

    def resolve_environment_dependencies(self, entities, options):
        '''Find latest environment dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(contexts, options)
        # Perform further environment specific resolves/checks on result here
        return versions

    def resolve_matte_painting_dependencies(self, entities, options):
        '''Find latest matte_painting dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further matte painting specific resolves/checks on result here
        return versions

    def resolve_prop_dependencies(self, entities, options):
        '''Find latest prop dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further prop specific resolves/checks on result here
        return versions

    def resolve_character_dependencies(self, entities, options):
        '''Find latest character dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further character specific resolves/checks on result here
        return versions

    def resolve_editing_dependencies(self, entities, options):
        '''Find latest editing dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further editing specific resolves/checks on result here
        return versions

    def resolve_production_dependencies(self, entities, options):
        '''Find latest production dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further production specific resolves/checks on result here
        return versions

    def resolve_modeling_dependencies(self, entities, options):
        '''Find latest modeling dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further modeling specific resolves/checks on result here
        return versions

    def resolve_previz_dependencies(self, entities, options):
        '''Find latest previz dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further previz specific resolves/checks on result here
        return versions

    def resolve_tracking_dependencies(self, entities, options):
        '''Find latest tracking dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further tracking specific resolves/checks on result here
        return versions

    def resolve_rigging_dependencies(self, entities, options):
        '''Find latest rigging dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further rigging specific resolves/checks on result here
        return versions

    def resolve_animation_dependencies(self, entities, options):
        '''Find latest animation dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further animation specific resolves/checks on result here
        return versions

    def resolve_fx_dependencies(self, entities, options):
        '''Find latest fx dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further fx specific resolves/checks on result here
        return versions

    def resolve_lighting_dependencies(self, entities, options):
        '''Find latest lighting dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further lighting specific resolves/checks on result here
        return versions

    def resolve_rotoscoping_dependencies(self, entities, options):
        '''Find latest rotoscoping dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further rotoscoping specific resolves/checks on result here
        return versions

    def resolve_compositing_dependencies(self, entities, options):
        '''Find latest compositing dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further compositing specific resolves/checks on result here
        return versions

    def resolve_deliverable_dependencies(self, entities, options):
        '''Find latest deliverable dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further deliverable specific resolves/checks on result here
        return versions

    def resolve_layout_dependencies(self, entities, options):
        '''Find latest layout dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further layout specific resolves/checks on result here
        return versions

    def resolve_rendering_dependencies(self, entities, options):
        '''Find latest rendering dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further rendering specific resolves/checks on result here
        return versions

    def resolve_concept_art_dependencies(self, entities, options):
        '''Find latest concept art dependency versions *contexts*, based on task type resolvable
        asset types supplied *options*'''
        versions = self.resolve_dependencies(entities, options)
        # Perform further concept art specific resolves/checks on result here
        return versions

    def resolve_task_dependencies(self, context, options):
        try:
            self.logger.info(
                'Resolving dependencies for {} {}({})'.format(
                    context.entity_type, context['name'], context['id']
                )
            )
            self._context = context  # Do not include deps on target context

            entities = []
            processed_entities = []

            # Fetch all linked asset containers (contexts: shots, asset builds, sequences and so on)
            self.get_linked_entities_recursive(
                context, entities, processed_entities
            )

            # Define task type resolver mappings
            TASK_TYPE_RESOLVERS = {
                'texture': self.resolve_texture_dependencies,
                'conform': self.resolve_conform_dependencies,
                'environment': self.resolve_environment_dependencies,
                'matte painting': self.resolve_matte_painting_dependencies,
                'prop': self.resolve_prop_dependencies,
                'character': self.resolve_character_dependencies,
                'editing': self.resolve_editing_dependencies,
                'production': self.resolve_production_dependencies,
                'modeling': self.resolve_modeling_dependencies,
                'previz': self.resolve_previz_dependencies,
                'tracking': self.resolve_tracking_dependencies,
                'rigging': self.resolve_rigging_dependencies,
                'animation': self.resolve_animation_dependencies,
                'fx': self.resolve_fx_dependencies,
                'lighting': self.resolve_lighting_dependencies,
                'rotoscoping': self.resolve_rotoscoping_dependencies,
                'compositing': self.resolve_compositing_dependencies,
                'deliverable': self.resolve_deliverable_dependencies,
                'layout': self.resolve_layout_dependencies,
                'rendering': self.resolve_rendering_dependencies,
                'concept art': self.resolve_concept_art_dependencies,
                '*': self.resolve_dependencies,
            }

            # Extract task type resolver options from schema
            resolver_options = options['task_types'].get(
                context['type']['name'].lower()
            )
            if resolver_options is None:
                # Options for this resolver not defined, any generic?
                resolver_options = options['task_types'].get('*')
                if resolver_options is None:
                    return (
                        {},
                        {
                            'message': 'No asset types defined to resolve for '
                            '"{}" task type!'.format(context['type']['name'])
                        },
                    )

            resolver_name = context['type']['name'].lower()
            if not resolver_name in TASK_TYPE_RESOLVERS:
                resolver_name = '*'

            if resolver_name in TASK_TYPE_RESOLVERS:
                self._status_names_include = options.get(
                    'status_names_include'
                )
                self._status_names_exclude = options.get(
                    'status_names_exclude'
                )
                return {
                    'versions': TASK_TYPE_RESOLVERS[resolver_name.lower()](
                        entities, resolver_options
                    )
                }
            else:
                return (
                    {},
                    {
                        'message': 'Do not know how to resolve task type: '
                        '"{}"'.format(context['type']['name'])
                    },
                )
        except:
            # Print exception as it might get squeezed further up
            import traceback

            sys.stderr.write(traceback.format_exc())
            raise

    def run(self, context_data=None, data=None, options=None):
        '''Retrieve a list of versions linked to the task given with *context* based on *options*'''

        # Load and check supplied context

        context_id = data['context_id']
        context = self.session.query(
            'Context where id={}'.format(context_id)
        ).first()
        if context is None:
            return (
                {},
                {
                    'message': 'The context {} is not known to ftrack!'.format(
                        context_id
                    )
                },
            )
        elif context.entity_type != 'Task':
            return (
                {},
                {
                    'message': 'Asset resolve can only be performed on tasks, not {}!'.format(
                        context_id
                    )
                },
            )
        # Load resolve options
        for key in ['max_link_depth', 'linked_only']:
            if key in options:
                setattr(self, key, options[key])
        return self.resolve_task_dependencies(context, options)


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonDefaultAssetManagerResolverPlugin(api_object)
    plugin.register()
