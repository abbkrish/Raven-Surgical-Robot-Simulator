"""
    DB related functions and classes.
    Author: Daniel Chen
    Created: 12/9/2014

    Mostly copied from (http://codereview.stackexchange.com/questions/39009/python-connection-with-mysql)
"""

import mysql.connector
import time
class NumpyConverter(mysql.connector.conversion.MySQLConverter):
    def _float32_to_mysql(self, value):
        return float(value)

    def _float64_to_mysql(self, value):
        return float(value)

    def _int32_to_mysql(self, value):
        return int(value)

    def _int64_to_mysql(self, value):
        return int(value)

class Mysql(object):
    __instance = None

    __host = None
    __user = None
    __password = None
    __database = None

    __session = None
    __connection = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Mysql, cls).__new__(cls, *args, **kwargs)
            return cls.__instance
    def __init__(self, host='localhost', user='root', password='', 
            database=''):
        self.__host = host
        self.__user = user
        self.__password = password
        self.__database = database

    # Open connection with database
    def _open(self):
        try:
            cnx = mysql.connector.connect(host=self.__host, 
                    user=self.__user, password=self.__password, 
                    database=self.__database)
            cnx.set_converter_class(NumpyConverter)
            self.__connection = cnx
            self.__session = cnx.cursor()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print 'Something is wrong with your user name or password'
            elif err.errno == errcode.ER_BAD_DB_ERROR:
                print 'Databse does not exist'
            else:
                print err

    def _close(self):
        self.__session.close()
        self.__connection.close()


    def _insert(self, table, *args, **kwargs):
        value = None
        query = "INSERT INTO %s " % table
        if kwargs:
            keys = kwargs.keys()
            values = kwargs.values()
            query += "(" + ",".join(["`%s`"]*len(keys)) % tuple(keys) + ") VALUES(" + ",".join(["%s"]*len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"]*len(values)) + ")"
        self.__session.execute(query, values)
        return self.__session.lastrowid

    def _commit(self):
        self.__connection.commit()

    def _rollback(self):
        self.__connection.rollback()

    def insert(self, table, *args, **kwargs):
        value = None
        query = "INSERT INTO %s " % table
        if kwargs:
            keys = kwargs.keys()
            values = kwargs.values()
            query += "(" + ",".join(["`%s`"]*len(keys)) % tuple(keys) + ") VALUES(" + ",".join(["%s"]*len(values)) + ")"
        elif args:
            values = args
            query += " VALUES(" + ",".join(["%s"]*len(values)) + ")"
        self._open()
        try:
            self.__session.execute(query, values)
            self.__connection.commit()
        except mysql.connector.Error as err:
            self.__connection.rollback()
            print err
            print "Error in: %s" %query
        self._close()
        return self.__session.lastrowid

    def select(self, table, where=None, *args):
        result = None
        query = "SELECT "
        keys = args
        l = len(keys) - 1
        for i, key in enumerate(keys):
            if key == '*':
                query += key
            else:
                query += "`"+key+"`"
            if i < l:
                query += ","
        query += " FROM %s" % table
        if where:
            query += " WHERE %s" % where
        self._open()
        try: 
            self.__session.execute(query)
            result = self.__session.fetchall()
        except mysql.connector.Error as err:
            print err
            print "Error in: %s" %query

        self._close()
        return result

    def update(self, table, index, **kwargs):
        query = "UPDATE %s SET" % table
        keys = kwargs.keys()
        values = kwargs.values()
        l = len(keys) -1
        for i, key in enumerate(keys):
            query += "`"+key+"`=%s"
            if i < 1:
                query += ","
        query += " WHERE index=%d" %index
        self._open()
        self.__session.execute(query, values)
        self.__connection.commit()
        self._close()

    def delete(self, table, index):
        query = "DELETE FROM %s WHERE uuid=%d" % (table, index)
        self._open()
        self.__session.execute(query)
        self.__connection.commit()
        self._close()

    def call_store_procedure(self, name, *args):
        result_sp = None
        self._open()
        self.__session.callproc(name, args)
        self.__connection.commit()
        for result in self.__session.stored_results():
            result_sp = result.fetchall()
        self._close()
        return result_sp

# Main code starts here
def test_mysql():
    connection = Mysql(host='130.126.140.209', user='root', password='Netlab1',database='raven')
    last_id = connection.insert('injection_summary', machine='daniel', timestamp=time.strftime('%Y-%m-%d %H:%M:%S'), parameter='this is a test')
    #print last_id
    results = connection.select('injection_summary', 'injection_id <= 5', '*', 'injection_id')
    for result in results:
        print result
