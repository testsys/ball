import urllib.request

import lang
import config
import db

conn, cur = db.mysql_init()

cur.execute('select id, url, name from events where state=1')
events = []
for row in cur.fetchall():
    events.append(list(row))

for event_id, event_url, event_name in events:
    contest_dat = urllib.request.urlopen(event_url).read()
    for line in contest_dat.split(b'\r\n'):
        if len(line) < 1 or line[0] != 64:
            continue
        dline = line.decode('cp1251')
        dl = dline.split()
        if dl[0] == '@s':
            pass
        elif dl[0] == '@p':
            prob = dline[3:].split(',')
            print('new problem: ' + prob[0])
        elif dl[0] == '@contest':
            name = dline[10:-1]
            if event_name != name:
                print('new contest name: ' + name)
                cur.execute('update events set name=%s where id=%s', [name, event_id])

conn.commit()
db.mysql_close(conn, cur)
