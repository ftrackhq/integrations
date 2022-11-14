# :coding: utf-8
# :copyright: Copyright (c) 2022 ftrack

from pymxs import runtime as rt

# Alembic default options
abc_default_import_options = {
    "CoordinateSystem": 3,
    "ImportToRoot": False,
    "FitTimeRange": True,
    "SetStartTime": False,
    "UVs": True,
    "Normals": True,
    "VertexColors": True,
    "ExtraChannels": True,
    "Velocity": True,
    "MaterialIDs": True,
    "Visibility": True,
    "CustomAttributes": True,
    "ShapeSuffix": True,
    "ObjectAttributes": True
}


def get_str_options(options):
    '''Return the given *options* + default ones to string'''
    job_args = []
    for k, v in abc_default_import_options.items():
        if k in list(options.keys()):
            job_args.append('{}={}'.format(k, options[k]))
        else:
            job_args.append('{}={}'.format(k, v))
    args_string = ';'.join(job_args)
    return args_string


def import_abc(file_path, options):
    '''Import the given the abc file from the given *file_path* with the
    given *options*'''
    for key, value in abc_default_import_options.items():
        if key in list(options.keys()):
            cmd = 'rt.AlembicImport.{} = {}'.format(key, options[key])
        else:
            cmd = 'rt.AlembicImport.{} = {}'.format(key, value)
        eval(cmd)

    rt.importFile(file_path, rt.name("noPrompt"), using="AlembicImport")

