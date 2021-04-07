# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import os
import logging
import sqlite3
import appdirs
import errno
import json
from json import JSONEncoder
import base64

from ftrack_connect_pipeline.log.log_item import LogItem

class ResultEncoder(JSONEncoder):
    ''' JSON encoder for handling non serializable objects in plugin result '''
    def default(self, obj):
        return str(obj)

class LogDB(object):
    table_name = 'LOGMGR'
    db_name = 'pipeline.db'
    _connection = None

    def __init__(self, name='default'):
        super(LogDB, self).__init__()
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        database_path = self.get_database_path()

        self._connection = sqlite3.connect(database_path)
        cur = self.connection.cursor()

        # Check if tables are created
        cur.execute(''' SELECT count(name) FROM sqlite_master WHERE'''
            ''' type='table' AND name='{0}' '''.format(self.table_name))

        if cur.fetchone()[0] == 0:
            cur.execute('''CREATE TABLE {0} (id INTEGER PRIMARY KEY,'''
                ''' status text,widget_ref text,'''
                ''' host_id text, execution_time real, plugin_name text,'''
                ''' result text, message text, user_message text,'''
                ''' plugin_type text)'''.format(self.table_name))
            self.connection.commit()
            self.logger.debug('Initialised plugin log persistent storage.')

        # Log out the file output.
        self.logger.info('Storing persistent log: {0}'.format(database_path))


    def __del__(self):
        self.connection.close()

    @property
    def connection(self):
        return self._connection

    def get_database_path(self):
        '''Get local persistent pipeline database path.

        Will create the directory (recursively) if it does not exist.

        Raise if the directory can not be created.
        '''

        user_data_dir = appdirs.user_data_dir('ftrack-connect', 'ftrack')

        if not os.path.exists(user_data_dir):
            try:
                os.makedirs(log_directory)
            except OSError as error:
                if error.errno == errno.EEXIST and os.path.isdir(log_directory):
                    pass
                else:
                    raise

        return os.path.join(user_data_dir, self.db_name)


    def add_log_item(self, log_item):
        # Store log record
        try:
            cur = self.connection.cursor()

            cur.execute('''INSERT INTO {0} (status,widget_ref,host_id,'''
                '''execution_time,plugin_name,result,message,user_message,'''
                '''plugin_type) VALUES (?,?,?,?,?,?,?,?,?)'''.format(
                    self.table_name), (
                log_item.status,
                log_item.widget_ref,
                log_item.host_id,
                log_item.execution_time,
                log_item.plugin_name,
                base64.encodebytes(
                    json.dumps(
                        log_item.result, cls=ResultEncoder).encode('utf-8')
                ).decode('utf-8'),
                log_item.message,
                log_item.user_message,
                log_item.plugin_type,
            ))
            self.connection.commit()

        except Exception as e:
            self.logger.error('Error storing log message in local persistent'
                ' database {}'.format(e))       

    def get_log_items(self, host_id):

        cur = self.connection.cursor()

        log_items = []
        if not host_id is None:
            cur.execute(''' SELECT status,widget_ref,host_id,execution_time,'''
                '''plugin_name,result,message,user_message,plugin_type FROM'''
                ''' {0} WHERE host_id=?;  '''.format(self.table_name), (
                    host_id, 
            ))

            for t in cur.fetchall():
                log_items.append(LogItem({
                    'status':t[0],
                    'widget_ref':t[1],
                    'host_id':t[2],
                    'execution_time':t[3],
                    'plugin_name':t[4],
                    'result':json.loads(base64.b64decode(t[5]).decode('utf-8')),
                    'message':t[6],
                    'user_message':t[7],
                    'plugin_type':t[8],
                }))
        return log_items
