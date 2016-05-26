#!/usr/bin/env python3

import urllib.request
import csv
import time

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
        dl = dline.split(' ', 1)
        if len(dl) < 2:
            continue
        mode = dl[0]
        data = None
        for row in csv.reader([dl[1]]):
            data = row
        if data == None:
            continue
        if mode == '@s':
            outcome = data[4]
            if outcome != 'OK':
                continue
            team_name, problem_letter = data[0], data[1]
            cur.execute('select id from teams where event_id=%s and name=%s', [event_id, team_name])
            team_id = None
            for row in cur.fetchall():
                team_id = row[0]
            cur.execute('select id from problems where event_id=%s and letter=%s', [event_id, problem_letter])
            problem_id = None
            for row in cur.fetchall():
                problem_id = row[0]
            balloon_id = None
            cur.execute('select id from balloons where event_id=%s and problem_id=%s and team_id=%s', [event_id, problem_id, team_id])
            for row in cur.fetchall():
                balloon_id = row[0]
            if balloon_id != None:
                print('have balloon: ' + str(balloon_id))
                continue
            cur.execute('insert into balloons(event_id, problem_id, team_id, state, time_created) values (%s, %s, %s, %s, %s)',
                [event_id, problem_id, team_id, 0, int(time.time())])
        elif mode == '@t':
            team_name, team_long_name = data[0], data[3]
            cur.execute('select id, long_name from teams where event_id=%s and name=%s', [event_id, team_name])
            team_id = None
            for row in cur.fetchall():
                team_id, old_team_long_name = row[0], row[1]
            if team_id == None:
                cur.execute('insert into teams(event_id, name, long_name) values (%s, %s, %s)', [event_id, team_name, team_long_name])
            else:
                if team_long_name != old_team_long_name:
                    cur.execute('update teams set long_name=%s where id=%s', [team_long_name, team_id])
        elif mode == '@p':
            problem_letter, problem_name = data[0], data[1]
            cur.execute('select id, name from problems where event_id=%s and letter=%s', [event_id, problem_letter])
            problem_id = None
            for row in cur.fetchall():
                problem_id, old_problem_name = row[0], row[1]
            if problem_id == None:
                cur.execute('insert into problems(event_id, letter, name) values (%s, %s, %s)', [event_id, problem_letter, problem_name])
            else:
                if problem_name != old_problem_name:
                    cur.execute('update problems set name=%s where id=%s', [problem_name, problem_id])
        elif mode == '@contest':
            name = data[0]
            if event_name != name:
                print('new contest name: ' + name)
                cur.execute('update events set name=%s where id=%s', [name, event_id])

conn.commit()
db.mysql_close(conn, cur)
