#!/usr/bin/env python3

import urllib.request
import csv
import time
import xml.etree.ElementTree as ET

import lang
import config
from db import DB

db = DB()
conn, cur = db.legacy()

cur.execute('select id, url, name from events where state=1')
events = []
for row in cur.fetchall():
    events.append(list(row))

team_cache = {}
problem_cache = {}
balloon_cache = {}

def team_load(event_id, team_name):
    global team_cache, cur
    if (event_id, team_name) not in team_cache:
        cur.execute(
            'select id from teams where event_id=%s and name=%s',
            [event_id, team_name])
        for row in cur.fetchall():
            team_cache[(event_id, team_name)] = row[0]
    return team_cache[(event_id, team_name)]

def problem_load(event_id, problem_letter):
    global problem_cache, cur
    if (event_id, problem_letter) not in problem_cache:
        cur.execute(
            'select id from problems where event_id=%s and letter=%s',
            [event_id, problem_letter])
        for row in cur.fetchall():
            problem_cache[(event_id, problem_letter)] = row[0]
    return problem_cache[(event_id, problem_letter)]


def parse_pcms(data, *, callback_ok, callback_team, callback_problem, callback_contest):
    root = ET.fromstring(data)
    assert root.tag == 'standings'
    for child in root:
        if child.tag == 'contest':
            contest = child
            break
        else:
            raise Exception("bad contest xml: not a contest in standings")
    else:
        raise Exception("bad contest xml: no contest found")
    callback_contest(contest.attrib['name'])
    for child in contest:
        if child.tag == 'challenge':
            for problem in child:
                callback_problem(problem.attrib['alias'], problem.attrib['name'])
        elif child.tag == 'session':
            callback_team(child.attrib['id'], child.attrib['party'])
            for problem in child:
                if int (problem.attrib['accepted']) == 1:
                    callback_ok(child.attrib['id'], problem.attrib['alias'])
        else:
            raise NotImplementedError("parse_pcms: tag '%s'" % child.tag)


def parse_testsys(data, *, callback_ok, callback_team, callback_problem, callback_contest):
    for line in data.split(b'\r\n'):
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
        if data is None:
            continue
        if mode == '@s':
            outcome = data[4]
            if outcome != 'OK':
                continue
            team_name, problem_letter = data[0], data[1]
            callback_ok(team_name, problem_letter)
        elif mode == '@t':
            team_name, team_long_name = data[0], data[3]
            callback_team(team_name, team_long_name)
        elif mode == '@p':
            problem_letter, problem_name = data[0], data[1]
            callback_problem(problem_letter, problem_name)
        elif mode == '@contest':
            name = data[0]
            callback_contest(name)



for event_id, event_url, event_name in events:
    cur.execute(
        'select id, problem_id, team_id from balloons' +
        ' where event_id=%s',
        [event_id])
    for row in cur.fetchall():
        balloon_id, problem_id, team_id = row
        balloon_cache[(event_id, problem_id, team_id)] = balloon_id
    haved_balloons = 0
    contest_dat = urllib.request.urlopen(event_url).read()

    def callback_ok(team_name, problem_letter):
        global cur, balloon_cache, haved_balloons
        team_id = team_load (event_id, team_name)
        problem_id = problem_load (event_id, problem_letter)
        if (event_id, problem_id, team_id) in balloon_cache:
            haved_balloons += 1
            return
        cur.execute(
            'insert into balloons' +
            '(event_id, problem_id, team_id, state, time_created)' +
            ' values (%s, %s, %s, %s, %s)',
            [event_id, problem_id, team_id, 0, int(time.time())]
        )

    def callback_team(team_name, team_long_name):
        global cur, team_cache
        cur.execute(
            'select id, long_name from teams' +
            ' where event_id=%s and name=%s',
            [event_id, team_name]
        )
        team_id = None
        for row in cur.fetchall():
            team_id, old_team_long_name = row[0], row[1]
        if team_id is None:
            cur.execute(
                'insert into teams(event_id, name, long_name)' +
                ' values (%s, %s, %s)',
                [event_id, team_name, team_long_name]
            )
            team_id = cur.lastrowid
        else:
            if team_long_name != old_team_long_name:
                cur.execute(
                    'update teams set long_name=%s where id=%s',
                    [team_long_name, team_id]
                )
        team_cache[(event_id, team_name)] = team_id

    def callback_problem(problem_letter, problem_name):
        global cur, problem_cache
        cur.execute(
            'select id, name from problems' +
            ' where event_id=%s and letter=%s',
            [event_id, problem_letter]
        )
        problem_id = None
        for row in cur.fetchall():
            problem_id, old_problem_name = row[0], row[1]
        if problem_id is None:
            cur.execute(
                'insert into problems(event_id, letter, name)' +
                ' values (%s, %s, %s)',
                [event_id, problem_letter, problem_name]
            )
            problem_id = cur.lastrowid
        else:
            if problem_name != old_problem_name:
                cur.execute(
                    'update problems set name=%s where id=%s',
                    [problem_name, problem_id]
                )
        problem_cache[(event_id, problem_letter)] = problem_id

    def callback_contest(name):
        global cur, event_name
        if event_name == name:
            return
        print('new contest name: ' + name)
        cur.execute(
            'update events set name=%s where id=%s',
            [name, event_id]
        )
        event_name = name

    for parser in [parse_pcms, parse_testsys]:
        try:
            parser(contest_dat, callback_ok=callback_ok, callback_team=callback_team, callback_problem=callback_problem, callback_contest=callback_contest)
            break
        except ET.ParseError:
            pass
    else:
        raise Exception("failed to parse monitor [%s]" % event_name)
    print('[%s] have cached balloons: %d' % (event_name, haved_balloons))

db.close(commit=True)

