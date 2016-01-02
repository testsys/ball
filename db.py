import cymysql

conn = False
cur = False

def mysql_init():
  conn = cymysql.connect( \
    host=config['db']['host'],
    user=config['db']['user'],
    passwd=config['db']['passwd'],
    db=config['db']['db'],
    charset='utf8')
  cur = conn.cursor()
  return conn, cur

def mysql_close(conn, cur):
  cur.close ()
  conn.close ()
