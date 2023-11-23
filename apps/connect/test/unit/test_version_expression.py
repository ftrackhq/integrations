# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import imp

import pytest


# Dynamically load default hook which has expression to test.
applicationsHookModule = imp.load_source(
    'ftrack_connect_hook_applications',
    os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'resource',
        'hook',
        'applications.py',
    ),
)


@pytest.mark.parametrize(
    ('path', 'expected'),
    [
        ('/Applications/Product 2014/Product Name 2014.app', '2014'),
        ('/Applications/Company/product2014/Product.app', '2014'),
        ('/Applications/Product7.0v10/Product7.0v10 PLE.app', '7.0v10'),
        ('/Applications/Product7.0v10b1a2.1/Product7.0v10.app', '7.0v10'),
        ('/Applications/Product7/Product7.0v10b1a2.1.app', '7.0v10b1a2.1'),
        (
            'C:\\Program Files(x86)\\Product 2014.8v12b353\\Product Name.exe',
            '2014.8v12b353',
        ),
        (
            'C:\\Program Files(x86)\\Product2014\\Product Name2014.8v12b353.exe',
            '2014.8v12b353',
        ),
        ('/path/to/2/product/1.2.3.4b2/product', '1.2.3.4b2'),
    ],
)
def test_extract_version(path, expected):
    '''Successfully extract version from path.'''
    match = applicationsHookModule.DEFAULT_VERSION_EXPRESSION.search(path)
    assert match is not None

    value = match.groupdict()['version']
    assert value == expected
