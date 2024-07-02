# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import copy


def get_tool_config_by_name(tool_configs, name):
    '''
    Return a tool-config with the given *name* from the *tool_configs*
    list.
    *tool_configs*: list of tool configs.
    '''
    for tool_config in tool_configs:
        if tool_config['name'] == name:
            return tool_config


def get_plugins(
    tool_config,
    filters=None,
    names_only=False,
    with_parents=False,
    _parents=None,
):
    '''
    Recursively return all the plugins available in the given tool_config.
    *tool_config*: Dictionary produced by the yaml loader.
    *filters*: dictionary with key and values to match for returned plugins
    *names_only*: return only name of the plugin.
    *with_parents*: return plugin with parent groups as a list.
    *_parents*: Internal use only.
    '''

    plugins = []
    # Check if it's a full tool-config or portion of it. If it's a portion it
    # might be a list.
    if isinstance(tool_config, dict):
        top_level = tool_config.get('engine', tool_config.get('plugins'))
    else:
        top_level = tool_config
    for obj in top_level:
        candidate = True
        if isinstance(obj, dict):
            if obj['type'] == 'group':
                # Recursively look for plugins into a group
                plugins.extend(
                    get_plugins(
                        obj.get('plugins'),
                        filters=filters,
                        names_only=names_only,
                        with_parents=with_parents,
                        _parents=(_parents or [])
                        + [{k: v for k, v in obj.items() if k != 'plugins'}],
                    )
                )
            elif obj['type'] == 'plugin':
                if filters:
                    for k, v in filters.items():
                        if isinstance(obj.get(k), list):
                            if not any(x in obj[k] for x in v):
                                candidate = False
                        elif isinstance(obj.get(k), str):
                            if obj[k] != v:
                                candidate = False
                        else:
                            candidate = False
                if candidate:
                    if names_only:
                        plugins.append(obj['plugin'])
                        continue
                    if with_parents:
                        obj = copy.deepcopy(obj)
                        obj['parents'] = _parents
                    plugins.append(obj)
                    continue
        if isinstance(obj, str):
            if filters:
                if 'plugin' not in list(filters.keys()):
                    candidate = False
                if candidate:
                    if obj != filters.get('plugin'):
                        candidate = False
            # Return single plugin
            if candidate:
                if with_parents:
                    plugin = {'plugin': obj}
                    plugin['parents'] = _parents
                    plugins.append(plugin)
                else:
                    plugins.append(obj)

    return plugins


def get_groups(tool_config, filters=None, top_level_only=True):
    '''
    Recursively return all the groups available in the given tool_config.
    *tool_config*: Dictionary produced by the yaml loader.
    *filters*: dictionary with key and values to match for returned plugins
    *top_level_only*: return only top level group, not recursive.
    '''

    groups = []
    # Check if it's a full tool-config or portion of it. If it's a portion it
    # might be a list.
    if isinstance(tool_config, dict):
        top_level = tool_config.get('engine', tool_config)
    else:
        top_level = tool_config
    for obj in top_level:
        candidate = True
        if isinstance(obj, dict):
            if obj['type'] == 'group':
                if not top_level_only:
                    groups.extend(
                        get_groups(
                            obj.get('plugins'),
                            filters=filters,
                            top_level_only=top_level_only,
                        )
                    )
                if filters:
                    for k, v in filters.items():
                        if isinstance(obj.get(k), list):
                            if not any(x in obj[k] for x in v):
                                candidate = False
                        elif isinstance(obj.get(k), dict):
                            for key, value in v.items():
                                if obj[k].get(key) != value:
                                    candidate = False
                        elif isinstance(obj.get(k), str):
                            if obj[k] != v:
                                candidate = False
                        else:
                            candidate = False
                if candidate:
                    groups.append(obj)
                    continue

    return groups
