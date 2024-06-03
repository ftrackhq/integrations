# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

logger = logging.getLogger(__name__)


def first_level_merge(root_extension_dict, override_dict):
    '''Override the root extension with a first level merge from the given override file'''
    return root_extension_dict.update(override_dict)


def set_overrides(current_extensions, new_extensions):
    '''If new extension from *new_extensions* found in *current_extensions* do a first level merge
    if YAML extensions'''
    non_python_extensions = ['js', 'config']
    for new_extension in new_extensions:
        existing_extension = None
        idx = None
        for idx, discovered_extension in enumerate(current_extensions):
            if (
                discovered_extension['extension_type']
                == new_extension['extension_type']
                and discovered_extension['name'] == new_extension['name']
            ):
                existing_extension = discovered_extension
                break
            elif (
                new_extension['extension_type'].split('_')[-1]
                not in non_python_extensions
            ):
                # Python extension - handle corner cases of dialogs plugins and widgets
                # when name is not the same but class name is the same, then we need to
                # override as well.
                if (
                    discovered_extension['extension_type']
                    == new_extension['extension_type']
                    and discovered_extension['extension'].__name__
                    == new_extension['extension'].__name__
                ):
                    existing_extension = discovered_extension
                    break
        if not existing_extension:
            # Add to discovered extensions
            current_extensions.append(new_extension)
        else:
            # Can we merge?
            if new_extension['extension_type'].endswith('_config'):
                logging.info(
                    f'Merging extension {existing_extension["name"]}({existing_extension["extension_type"]} @'
                    f' {existing_extension["path"]}) on top of {new_extension["name"]}'
                    f'({new_extension["extension_type"]} @ {new_extension["path"]}).'
                )
                # Have the latter extension be overridden by the former
                first_level_merge(
                    existing_extension['extension'], new_extension['extension']
                )
            else:
                # Make sure we replace the previous discovered extensions with the new one.
                current_extensions[idx] = new_extension
    return current_extensions
