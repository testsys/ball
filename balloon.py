#!/usr/bin/env python3


class Balloon:
    __slots__ = ['id', 'team_id', 'problem_id', 'volunteer_id', 'state']
    def __init__(self, b):
        self.id = b['id']
        self.team_id = b['team_id']
        self.problem_id = b['problem_id']
        self.volunteer_id = b['volunteer_id']
        self.state = b['state']


