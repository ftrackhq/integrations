# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
import sqlite3
import appdirs
import errno
import json
from json import JSONEncoder
import base64
import traceback
import datetime
import time

from ftrack_framework_core.log.log_item import LogItem


class ResultEncoder(JSONEncoder):
    '''JSON encoder for handling non serializable objects in plugin result'''

    def default(self, obj):
        return str(obj)


# TODO: review this class to make it easier to maintain.
#  Define all keys in a common place.
# noinspection SpellCheckingInspection
class LogDB(object):
    '''
    Log database class
    '''

    db_name = 'framework-{}.db'
    table_name = 'LOGMGR'
    database_expire_grace_s = 7 * 24 * 3600
    _connection = None
    _database_path = None

    def __init__(self, host_id, db_name=None, table_name=None):
        '''
        Initializes a new persistent local log database having
        database name *db_name* on disk and *table_name* table name.
        '''
        super(LogDB, self).__init__()

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        if db_name:
            self.db_name = db_name
        if table_name:
            self.table_name = table_name

        print(self.table_name)

        self._database_path = self.get_database_path(host_id)

        self._connection = sqlite3.connect(
            self._database_path, check_same_thread=False
        )
        cur = self.connection.cursor()

        # Check if tables are created
        cur.execute(
            ''' SELECT count(name) FROM sqlite_master WHERE'''
            ''' type='table' AND name='{0}' '''.format(self.table_name)
        )

        if cur.fetchone()[0] == 0:
            cur.execute(
                '''CREATE TABLE {0} (id INTEGER PRIMARY KEY,'''
                ''' date int, plugin_status text, plugin_boolean_status bool, host_id text, plugin_name text,'''
                ''' plugin_type text, plugin_id text, host_type text, plugin_method text,'''
                ''' plugin_method_result text, plugin_result_registry text,'''
                ''' plugin_execution_time real,'''
                ''' plugin_message text, plugin_context_data text,'''
                ''' plugin_data text, plugin_options text,'''
                ''' plugin_widget_id text, plugin_widget_name text)'''.format(
                    self.table_name
                )
            )

            self.connection.commit()
            self.logger.debug('Initialised plugin log persistent storage.')

        # Log out the file exporters.
        self.logger.info(
            'Storing persistent log: {0}'.format(self._database_path)
        )

    def __del__(self):
        '''Release resources (called mostly, not by all DCC apps)'''
        self.connection.close()
        if not self._database_path is None:
            # Delete database from disk
            self.logger.info(
                'Removing database @ {}'.format(self._database_path)
            )
            try:
                os.remove(self._database_path)
                self._database_path = None
            except Exception:
                self.logger.warning(traceback.format_exc())

    @property
    def connection(self):
        return self._connection

    def get_database_path(self, host_id):
        '''Get local persistent pipeline database path.

        Will create the directory (recursively) if it does not exist.

        Raise if the directory can not be created.
        '''

        user_data_dir = appdirs.user_data_dir('ftrack-connect', 'ftrack')

        if not os.path.exists(user_data_dir):
            try:
                os.makedirs(user_data_dir)
            except OSError as error:
                if error.errno == errno.EEXIST and os.path.isdir(
                    user_data_dir
                ):
                    pass
                else:
                    raise
        else:
            # Check for and remove expired db:s older than one week by default

            date_grace = datetime.datetime.now() - datetime.timedelta(
                seconds=self.database_expire_grace_s
            )

            for filename in os.listdir(user_data_dir):
                if not filename.lower().endswith('.db'):
                    continue
                db_path = os.path.join(user_data_dir, filename)
                date_modified = datetime.datetime.fromtimestamp(
                    os.path.getmtime(db_path)
                )
                if date_modified <= date_grace:
                    self.logger.info(
                        'Removing expired local persistent database: '
                        '{}'.format(filename)
                    )
                    try:
                        os.remove(db_path)
                    except Exception as e:
                        self.logger.error(e)

        return os.path.join(user_data_dir, self.db_name.format(host_id))

    def add_log_item(self, log_item):
        '''
        Stores a :class:`~ftrack_framework_core.log.log_item.LogItem` in
        persistent log database.
        '''
        try:
            cur = self.connection.cursor()

            cur.execute(
                '''INSERT INTO {0} (date,plugin_status,plugin_boolean_status,
                host_id,plugin_name,plugin_type,plugin_id,host_type,plugin_method,
                plugin_method_result,plugin_result_registry,plugin_execution_time,
                plugin_message,plugin_context_data,plugin_data,plugin_options,
                plugin_widget_id,plugin_widget_name) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''.format(
                    self.table_name
                ),
                (
                    time.time(),
                    log_item.plugin_status,
                    log_item.plugin_boolean_status,
                    log_item.host_id,
                    log_item.plugin_name,
                    log_item.plugin_type,
                    log_item.plugin_id,
                    log_item.host_type,
                    log_item.plugin_method,
                    # TODO: Check previous versions to deal with Json in plugin result
                    str(log_item.plugin_method_result),
                    str(log_item.plugin_result_registry),
                    log_item.plugin_execution_time,
                    log_item.plugin_message,
                    str(log_item.plugin_context_data),
                    str(log_item.plugin_data),
                    str(log_item.plugin_options),
                    str(log_item.plugin_widget_id),
                    str(log_item.plugin_widget_name),
                ),
            )
            self.connection.commit()

        except sqlite3.Error as e:
            self.logger.error(
                'Error storing log message in local persistent'
                ' database {}'.format(e)
            )

    def get_log_items(self, host_id):
        '''
        Stores a :class:`~ftrack_framework_core.log.log_item.LogItem` in
        persistent log database.
        '''

        cur = self.connection.cursor()

        log_items = []
        if not host_id is None:
            cur.execute(
                ''' SELECT date,plugin_status,plugin_boolean_status,host_id,'''
                '''plugin_name,plugin_type,'''
                '''plugin_id,host_type,plugin_method,plugin_method_result,'''
                '''plugin_result_registry,plugin_execution_time,'''
                '''plugin_message,plugin_context_data,plugin_data,plugin_options'''
                '''plugin_widget_id,plugin_widget_name'''
                ''' FROM {0} WHERE host_id=?;  '''.format(self.table_name),
                (host_id,),
            )

            for t in cur.fetchall():
                log_items.append(
                    LogItem(
                        {
                            'date': datetime.datetime.fromtimestamp(t[0]),
                            'plugin_status': t[1],
                            'plugin_boolean_status': t[2],
                            'host_id': t[3],
                            'plugin_name': t[4],
                            'plugin_type': t[5],
                            'plugin_id': t[6],
                            'host_type': t[7],
                            'plugin_method': t[8],
                            # TODO: Check previous versions to deal with Json in plugin result
                            'plugin_method_result': t[9],
                            'plugin_result_registry': t[10],
                            'plugin_execution_time': t[11],
                            'plugin_message': t[12],
                            'plugin_context_data': t[13],
                            'plugin_data': t[14],
                            'plugin_options': t[15],
                            'plugin_widget_id': t[16],
                            'plugin_widget_name': t[17],
                        }
                    )
                )
        return log_items

    def get_log_items_by_plugin_id(self, host_id, plugin_id):
        '''
        Stores a :class:`~ftrack_framework_core.log.log_item.LogItem` in
        persistent log database.
        '''

        cur = self.connection.cursor()

        log_items = []
        if not host_id is None:
            cur.execute(
                ''' SELECT date,plugin_status,plugin_boolean_status,host_id,'''
                '''plugin_name,plugin_type,'''
                '''plugin_id,host_type,plugin_method,plugin_method_result,plugin_result_registry,'''
                '''plugin_execution_time,plugin_message,plugin_context_data,'''
                '''plugin_data,plugin_options,plugin_widget_id,plugin_widget_name'''
                ''' FROM {0} WHERE host_id=? AND plugin_id=?;  '''.format(
                    self.table_name
                ),
                (host_id, plugin_id),
            )

            for t in cur.fetchall():
                log_items.append(
                    LogItem(
                        {
                            'date': datetime.datetime.fromtimestamp(t[0]),
                            'plugin_status': t[1],
                            'plugin_boolean_status': t[2],
                            'host_id': t[3],
                            'plugin_name': t[4],
                            'plugin_type': t[5],
                            'plugin_id': t[6],
                            'host_type': t[7],
                            'plugin_method': t[8],
                            # TODO: Check previous versions to deal with Json in plugin result
                            'plugin_method_result': t[9],
                            'plugin_result_registry': t[10],
                            'plugin_execution_time': t[11],
                            'plugin_message': t[12],
                            'plugin_context_data': t[13],
                            'plugin_data': t[14],
                            'plugin_options': t[15],
                            'plugin_widget_id': t[16],
                            'plugin_widget_name': t[17],
                        }
                    )
                )
        return log_items
