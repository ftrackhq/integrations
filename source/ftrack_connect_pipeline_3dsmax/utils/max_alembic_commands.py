# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import MaxPlus

import math

from custom_commands import eval_max_script

# Alembic default options
abc_default_import_options = {
    "CoordinateSystem": 3,
    "ImportToRoot": 'false',
    "FitTimeRange": 'true',
    "SetStartTime": 'false',
    "UVs": 'true',
    "Normals": 'true',
    "VertexColors": 'true',
    "ExtraChannels": 'true',
    "Velocity": 'true',
    "MaterialIDs": 'true',
    "Visibility": 'true',
    "CustomAttributes": 'true',
    "ShapeSuffix": 'true',
    "ObjectAttributes": 'true'
}


def get_str_options(options):
    job_args = []
    for k, v in abc_default_import_options.iteritems():
        if k in options.keys():
            job_args.append('{}={}'.format(k, options[k]))
        else:
            job_args.append('{}={}'.format(k, v))
    args_string = ';'.join(job_args)
    return args_string


def import_abc(file_path, options):
    options_args = ''''''
    for key, value in abc_default_import_options.iteritems():
        if key in options.keys():
            options_args = (
                    options_args + '''AlembicImport.{0} = {1} \n'''.format(
                key, options[key])
            )
        else:
            options_args = (
                    options_args + '''AlembicImport.{0} = {1} \n'''.format(
                key, value)
            )

    cmd = '''
        {0}
        importFile(@"{1}") #noPrompt using:AlembicImport
        '''.format(options_args, file_path)

    eval_max_script(cmd)
