import cymysql

import config

conn = False
cur = False

def mysql_init():
    dbc = config.config['db']
    conn = cymysql.connect( \
        host=dbc['host'],
        user=dbc['user'],
        passwd=dbc['passwd'],
        db=dbc['db'],
        charset='utf8')
    cur = conn.cursor()
    return conn, cur

def mysql_close(conn, cur):
    cur.close()
    conn.close()
