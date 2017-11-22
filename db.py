try:
    import cymysql
except ImportError:
    import pymysql as cymysql

import config


class DB:
    def __init__(self):
        dbc = config.config['db']
        self.__connection = cymysql.connect(
            host=dbc['host'],
            user=dbc['user'],
            passwd=dbc['passwd'],
            db=dbc['db'],
            charset='utf8'
        )
        self.__cursor = self.__connection.cursor()

    def close(self, *, commit=False):
        if commit:
            self.__connection.commit()
        self.__cursor.close()
        self.__connection.close()

    def event(self, event_id):
        self.__cursor.execute(
            'select id, name, state, url from events' +
            ' where id=%s',
            [event_id]
        )
        for row in self.__cursor.fetchall():
            return row
        raise KeyError(event_id)

    def events(self):
        events = []
        self.__cursor.execute('select id, name, state from events')
        for row in self.__cursor.fetchall():
            events.append(row)
        return events

    def event_add(self, state, url):
        self.__cursor.execute(
            'insert into events (state, url) values (%s, %s)',
            [state, url]
        )

    def problem(self, problem_id):
        self.__cursor.execute(
            'select id, letter, color, name from problems' +
            ' where id=%s',
            [problem_id]
        )
        for row in self.__cursor.fetchall():
            return {
                'id': row[0],
                'letter': row[1],
                'color': row[2],
                'name': row[3]
            }
        raise KeyError(problem_id)

    def problems(self, event_id):
        problems = []
        self.__cursor.execute(
            'select id, letter, color from problems' +
            ' where event_id=%s',
            [event_id]
        )
        for row in self.__cursor.fetchall():
            p = {
                'id': row[0],
                'letter': row[1],
                'color': row[2]
            }
            problems.append(p)
        return problems

    def problem_color(self, problem_id, color):
        self.__cursor.execute(
            'update problems set color=%s where id=%s',
            [color, problem_id]
        )

    def __balloons_filter(self, event_id, where, values=[]):
        fields = ', '.join(
            ['id', 'problem_id', 'team_id', 'volunteer_id', 'state']
        )
        self.__cursor.execute(
            'select ' + fields +
            ' from balloons where event_id=%s '+ where +
            ' order by state, id desc',
            [event_id] + values
        )
        balloons = []
        for row in self.__cursor.fetchall():
            b = {
                'id': row[0],
                'problem_id': row[1],
                'team_id': row[2],
                'volunteer_id': row[3],
                'state': int(row[4])
            }
            balloons.append(b)
        return balloons

    def balloons_new(self, event_id):
        return self.__balloons_filter(event_id, 'and state<100')

    def balloons_old(self, event_id):
        return self.__balloons_filter(event_id, 'and state>=100')

    def balloons_my(self, event_id, user_id):
        return self.__balloons_filter(event_id, 'and state>=100 and state<200 and volunteer_id=%s', [user_id])

    def balloons_count(self, event_id, problem_id):
        self.__cursor.execute(
            'select count(*) from balloons' +
            ' where event_id=%s and problem_id=%s',
            [event_id, problem_id]
        )
        cnt = 0
        for row in self.__cursor.fetchall():
            return int(row[0])
        raise WhatTheException()

    def balloon_take(self, balloon_id, user_id):
        self.__cursor.execute(
            'update balloons set state=101, volunteer_id=%s where id=%s',
            [user_id, balloon_id]
        )

    def balloon_done(self, balloon_id, user_id):
        self.__cursor.execute(
            'update balloons set state=201, volunteer_id=%s where id=%s',
            [user_id, balloon_id]
        )

    def balloon_drop(self, balloon_id):
        self.__cursor.execute(
            'update balloons set state=1 where id=%s', [balloon_id]
        )

    def teams(self, event_id):
        teams = []
        self.__cursor.execute(
            'select id, name, long_name from teams' +
            ' where event_id=%s',
            [event_id]
        )
        for row in self.__cursor.fetchall():
            t = {
                'id': row[0],
                'name': row[1],
                'long_name': row[2]
            }
            teams.append(t)
        return teams

    def fts(self, event_id, *, problem_id=None, team_id=None):
        self.__cursor.execute(
            'select id from balloons' +
            ' where event_id=%s' +
            (' and problem_id=%s' if problem_id is not None else '') +
            (' and team_id=%s' if team_id is not None else '') +
            ' order by id limit 1',
            list (filter (lambda x: x is not None, [event_id, problem_id, team_id]))
        )
        for row in self.__cursor.fetchall():
            return row[0]
        raise KeyError

