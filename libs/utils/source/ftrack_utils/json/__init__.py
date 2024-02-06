# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import logging
import json

logger = logging.getLogger(__name__)


def read_json_file(file_path):
    '''Read the given *file_path* json file'''
    content = None
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                content = json.load(file)
            except Exception:
                logger.exception(
                    f'Exception reading json file in {file_path}.'
                )
    else:
        logger.warning(f"file {file_path} doesn't exists")

    return content or dict()


def write_json_file(file_path, content):
    '''Write the given *file_path* json file with the given *content*'''
    with open(file_path, 'w') as file:
        try:
            json.dump(content, file, indent=4)
        except Exception as e:
            logger.exception(
                f'Exception writing json file in {file_path}, error:{e}.'
            )
