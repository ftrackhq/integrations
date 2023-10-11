# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack


class ConnectError(Exception):
    '''Base ftrack connect error.'''

    pass


class NotUniqueError(ConnectError):
    '''Raise when something that should be unique is not.'''


class InvalidStateError(ConnectError):
    '''Raise when an invalid state is detected for current action.'''


class ParseError(ConnectError):
    '''Raise when a parsing action fails.'''
