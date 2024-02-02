# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import logging
import sqlite3
import platformdirs
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
                ''' date int, status text, boolean_status bool,'''
                ''' host_id text, name text,'''
                ''' reference text,'''
                ''' execution_time real,'''
                ''' message text, options text,'''
                ''' store text)'''.format(self.table_name)
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

        user_data_dir = platformdirs.user_data_dir('ftrack-connect', 'ftrack')

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

    def add_log_item(self, host_id, log_item):
        '''
        Stores a :class:`~ftrack_framework_core.log.log_item.LogItem` in
        persistent log database.
        '''
        try:
            cur = self.connection.cursor()

            cur.execute(
                '''INSERT INTO {0} (date,status,boolean_status,
                host_id, name,reference,
                execution_time,
                message,options,store) 
                VALUES (?,?,?,?,?,?,?,?,?,?)'''.format(
                    self.table_name
                ),
                (
                    time.time(),
                    log_item.status,
                    log_item.boolean_status,
                    host_id,
                    log_item.name,
                    log_item.reference,
                    log_item.execution_time,
                    log_item.message,
                    str(log_item.options),
                    str(log_item.store),
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
                ''' SELECT date,status,boolean_status,host_id,'''
                '''name,'''
                '''reference,'''
                '''execution_time,'''
                '''message,options,store'''
                ''' FROM {0} WHERE host_id=?;  '''.format(self.table_name),
                (host_id,),
            )

            for t in cur.fetchall():
                log_items.append(
                    LogItem(
                        {
                            'date': datetime.datetime.fromtimestamp(t[0]),
                            'status': t[1],
                            'boolean_status': t[2],
                            'host_id': t[3],
                            'name': t[4],
                            'reference': t[5],
                            'execution_time': t[6],
                            'message': t[7],
                            'options': t[8],
                            'store': t[9],
                        }
                    )
                )
        return log_items

    def get_log_items_by_reference(self, host_id, reference):
        '''
        Stores a :class:`~ftrack_framework_core.log.log_item.LogItem` in
        persistent log database.
        '''

        cur = self.connection.cursor()

        log_items = []
        if not host_id is None:
            cur.execute(
                ''' SELECT date,status,boolean_status,host_id,'''
                '''name,'''
                '''reference,'''
                '''execution_time,message,'''
                '''options,store'''
                ''' FROM {0} WHERE host_id=? AND reference=?;  '''.format(
                    self.table_name
                ),
                (host_id, reference),
            )

            for t in cur.fetchall():
                log_items.append(
                    LogItem(
                        {
                            'date': datetime.datetime.fromtimestamp(t[0]),
                            'status': t[1],
                            'boolean_status': t[2],
                            'host_id': t[3],
                            'name': t[4],
                            'reference': t[5],
                            'execution_time': t[6],
                            'message': t[7],
                            'options': t[8],
                            'store': t[9],
                        }
                    )
                )
        return log_items
