#!/usr/bin/env python3

from flask import (
    Flask, url_for, render_template, request, make_response, redirect)
import cgi
import hashlib
import time
import random
import string
import urllib
import json
import logging

import lang
import config
from db import DB

ball = Flask(__name__)


@ball.route('/')
def index():
    db = DB()
    user_id, auth_html = check_auth(request)
    content = ''
    events = db.events()
    if len(events) == 0:
        content = lang.lang['index_no_events']
    for e in events:
        content += (
            '<div><a href="' + config.base_url + '/event' + str(e[0]) + '">' +
            cgi.escape(e[1]) + '</a></div>\n')
    if user_id:
        content += (
            '<div><form action="do_add_event" method="POST">' +
            '<input type="text" placeholder="' +
            lang.lang['index_monitor_url'] + '" name="url" />' +
            '<input type="submit" value="' +
            lang.lang['index_add_event'] + '" />' +
            '</form></div>\n')
    db.close()
    return render_template(
        'template.html',
        title=lang.lang['index_title'],
        auth=auth_html,
        base=config.base_url,
        content=content)


@ball.route('/do_add_event', methods=['POST'])
def do_add_event():
    db = DB()
    user_id, auth_html = check_auth(request)
    if user_id not in config.allowed_users:
        return redirect(config.base_url, code=307)
    try:
        event_url = request.form['url']
    except:
        return redirect(config.base_url)
    db.event_add(1, event_url)
    db.close(commit=True)
    return redirect(config.base_url)


@ball.route('/problem<int:problem_id>')
def problem(problem_id):
    user_id, auth_html = check_auth(request)
    if user_id not in config.allowed_users:
        return redirect(config.base_url)
    db = DB()
    problem_id = int(problem_id)
    content = ''
    colors = [
        '#f9ff0f', '#000000', '#f6ab23', '#cc0000',
        '#03C03C', '#e1379e', '#9e37e1', '#2FACAC',
        '#0047AB', '#FFFFF']
    problems = [db.problem(problem_id)]
    problems_html = (
        '<h2>' + problems[0]['letter'] + ': ' +
        problems[0]['name'] + '</h2>\n')
    content += problems_html
    colors_html = ''
    colors_html += (
        '<div><span style="color:' + problems[0]['color'] + '">' +
        lang.lang['problem_cur_color'] +
        ' <b>' + problems[0]['color'] + '</b>' + '</span></div>')
    for c in colors:
        colors_html += (
            '<div><a href="' + config.base_url + '/do_set_color?problem=' +
            str(problem_id) + '&color=' + urllib.parse.quote(c) +
            '"><span style="color:' + c + '">' +
            lang.lang['problem_set_color'] +
            ' <b>' + c + '</b>' + '</span></a></div>')
    content += colors_html
    db.close()
    return render_template(
        'template.html',
        title=problems[0]['letter'],
        auth=auth_html,
        base=config.base_url,
        content=content)


def get_state_str_current(event_id, b):
    state_str = ''
    state_str += (
        ' <a href="' + config.base_url + '/do_done?event=' + str(event_id) +
        '&balloon=' + str(b['id']) + '">' +
        lang.lang['event_queue_done'] + '</a>')
    state_str += (
        ' <a href="' + config.base_url + '/do_drop?event=' + str(event_id) +
        '&balloon=' + str(b['id']) + '">' +
        lang.lang['event_queue_drop'] + '</a>')
    return state_str


def get_state_str_queue(event_id, b):
    state_str = ''
    if b['state'] >= 0 and b['state'] < 100:
        state_str = (
            lang.lang['balloon_state_wanted'] +
            ' <a href="' + config.base_url + '/do_take?event=' + str(event_id) +
            '&balloon=' + str(b['id']) + '">' +
            lang.lang['event_queue_take'] + '</a>')
    elif b['state'] < 200:
        state_str = lang.lang['balloon_state_carrying']
    elif b['state'] < 300:
        state_str = lang.lang['balloon_state_delivered']
    else:
        state_str = lang.lang['balloon_state_error']
    if str(b['volunteer_id']) != '':
        state_str += ' (' + str(b['volunteer_id']) + ')'
    return state_str


@ball.route('/event<int:event_id>')
def event(event_id):
    user_id, auth_html = check_auth(request)
    if user_id not in config.allowed_users:
        return redirect(config.base_url)
    db = DB()
    event_id = int(event_id)
    content = ''
    try:
        e = db.event(event_id)
    except KeyError:
        e = None
    if e is None:
        return redirect(config.base_url)
    event = {
        'name': e[1],
        'state': e[2],
        'url': e[3]}
    event_html = ''
    event_html += (
        '<div><a href="' + cgi.escape(event['url']) + '">' +
        lang.lang['event_header_monitor_link'] + '</a></div>\n')
    content += event_html

    problems = db.problems(event_id)
    problems_map = {p['id']: i for i, p in enumerate (problems)}
    for p in problems:
        cnt = db.balloons_count(event_id, p['id'])
        p['cnt'] = cnt
    problems_html = '<h2>' + lang.lang['event_header_problems'] + '</h2>\n'
    problems_html += '<table style="width: 100%;"><tr>'
    for p in problems:
        text = '&nbsp;'
        if p['color'] == '':
            text = '?'
        problems_html += (
            '<td class="balloons_problem_color" style="' +
            'background-color: ' + p['color'] + ';">' +
            text + '</td>')
        problems_html += (
            '<td class="balloons_problem_letter">' +
            '<a href="' + config.base_url + '/problem' + str(p['id']) + '">' +
            p['letter'] + '</a>' +
            '(' + str(p['cnt']) + ')' + '</td>')
    problems_html += '</tr></table>\n'
    content += problems_html

    teams = db.teams(event_id)
    teams_map = {t['id']: i for i, t in enumerate (teams)}

    first_to_solve = {}
    for p in problems:
        try:
            first_to_solve[p['id']] = db.fts(event_id, problem_id=p['id'])
        except KeyError:
            pass

    first_solved = {}
    for t in teams:
        try:
            first_solved[t['id']] = db.fts(event_id, team_id=t['id'])
        except KeyError:
            pass

    def get_balloons_html(header, get_state_str, balloons):
        if len(balloons) == 0:
            return ''
        balloons_html = '<h2>' + header + '</h2>\n'
        balloons_html += '<table style="width: 100%;">\n'
        for b in balloons:
            p = problems[problems_map[b['problem_id']]]
            t = teams[teams_map[b['team_id']]]
            state_str = get_state_str(event_id, b)
            balloons_html += '<tr class="balloons_row">'
            balloons_text = '&nbsp;'
            if not p['color']:
                balloons_text = '?'
            balloons_html += (
                '<td class="balloons_balloon_color"' +
                ' style="background-color: ' + p['color'] + '">' +
                balloons_text + '</td>')
            x = ''
            if first_to_solve[b['problem_id']] == b['id']:
                x = '<b>' + lang.lang['event_queue_first_to_solve'] + '</b>'
            balloons_html += (
                '<td>' + x + lang.lang['event_queue_problem'] +
                ' <b>' + p['letter'] + '</b></td>')
            x = ''
            if b['team_id'] in first_solved:
                if first_solved[b['team_id']] == b['id']:
                    x = '<b>' + lang.lang['event_queue_first_solved'] + '</b>'
            balloons_html += (
                '<td>' + x + lang.lang['event_queue_team'] +
                ' <b>' + t['name'] + '</b>: ' +
                cgi.escape(t['long_name']) + '</td>')
            balloons_html += '<td>' + state_str + '</td>'
            balloons_html += '<tr>\n'
        balloons_html += '</table>\n'
        return balloons_html

    balloons = db.balloons_my(event_id, user_id)
    content += get_balloons_html(
        lang.lang['event_header_your_queue'],
        get_state_str_current, balloons)

    balloons = db.balloons_new(event_id)
    content += get_balloons_html(
        lang.lang['event_header_offer'],
        get_state_str_queue, balloons)

    balloons = db.balloons_old(event_id)
    content += get_balloons_html(
        lang.lang['event_header_queue'],
        get_state_str_queue, balloons)

    db.close()
    return render_template(
        'template.html',
        title=event['name'],
        base=config.base_url,
        content=content)


@ball.route('/do_take')
def do_take():
    user_id, auth_html = check_auth(request)
    if user_id not in config.allowed_users:
        return redirect(config.base_url)
    db = DB()
    try:
        event_id = int(request.args.get('event', '0'))
        balloon_id = int(request.args.get('balloon', '0'))
    except:
        return redirect(config.base_url)
    db.balloon_take(balloon_id, user_id)
    db.close(commit=True)
    return redirect(config.base_url + '/event' + str(event_id))


@ball.route('/do_done')
def do_done():
    user_id, auth_html = check_auth(request)
    if user_id not in config.allowed_users:
        return redirect(config.base_url)
    db = DB()
    try:
        event_id = int(request.args.get('event', '0'))
        balloon_id = int(request.args.get('balloon', '0'))
    except:
        return redirect(config.base_url)
    db.balloon_done(balloon_id, user_id)
    db.close(commit=True)
    return redirect(config.base_url + '/event' + str(event_id))


@ball.route('/do_drop')
def do_drop():
    user_id, auth_html = check_auth(request)
    if user_id not in config.allowed_users:
        return redirect(config.base_url)
    db = DB()
    try:
        event_id = int(request.args.get('event', '0'))
        balloon_id = int(request.args.get('balloon', '0'))
    except:
        return redirect(config.base_url)
    db.balloon_drop(balloon_id)
    db.close(commit=True)
    return redirect(config.base_url + '/event' + str(event_id))


@ball.route('/do_set_color')
def do_set_color():
    user_id, auth_html = check_auth(request)
    if user_id not in config.allowed_users:
        return redirect(config.base_url)
    db = DB()
    try:
        problem_id = int(request.args.get('problem', '0'))
        color = request.args.get('color', '')
    except:
        return redirect(config.base_url)
    db.problem_color(problem_id, color)
    db.close(commit=True)
    return redirect(config.base_url + '/problem' + str(problem_id))


def create_auth_token(user_id):
    day = int(time.time() / (24 * 60 * 60))
    return hashlib.md5((
        str(user_id) + ':' +
        str(day) + ':' +
        config.auth_salt).encode()).hexdigest()


def check_auth(request):
    auth_html = (
        '<div>' + lang.lang['index_not_authorised'] +
        ' <a href="' + config.base_url + 'auth">' +
        lang.lang['index_log_in'] +
        '</a></div>\n')
    try:
        user_id = request.cookies.get('ball_user_id')
        auth_token = request.cookies.get('ball_auth_token')
    except:
        return None, auth_html
    if auth_token != create_auth_token(user_id):
        return None, auth_html
    auth_html = '<div><b>' + str(user_id) + '</b></div>\n'
    return user_id, auth_html


@ball.route('/auth')
def auth():
    user_id, auth_html = check_auth(request)
    content = ''
    content += (
        '<div><a href="' +
        config.base_url +
        '/auth/vk/start">VK</a></div>')
    content += (
        '<div><a href="' +
        config.base_url +
        '/auth/google/start">Google</a></div>')
    return render_template(
        'template.html',
        title=lang.lang['auth'],
        auth=auth_html,
        base=config.base_url,
        content=content)


@ball.route('/auth/vk/start')
def auth_vk_start():
    return redirect(
        'https://oauth.vk.com/authorize?' +
        'client_id=' + config.vk_app_id +
        '&display=page' +
        '&response_type=code' +
        '&redirect_uri=' + config.base_url_global + '/auth/vk/done')


@ball.route('/auth/vk/done')
def auth_vk_done():
    try:
        code = request.args.get('code', '')
    except:
        code = 'None'
    vk_oauth_url = (
        'https://oauth.vk.com/access_token?client_id=' +
        config.vk_app_id + '&client_secret=' + config.vk_client_secret +
        '&redirect_uri=' + config.base_url_global + '/auth/vk/done&code=' +
        code)
    ball.logger.debug ('vk_oauth_url: ' + vk_oauth_url)
    res = json.loads(urllib.request.urlopen(vk_oauth_url).read().decode())
    if 'error' in res:
        error_content = 'Failed auth: ' + str(res['error_description'])
        return render_template(
            'template.html',
            title='Failed auth',
            base=config.base_url,
            content=error_content)
    user_id = 'vk:' + str(res['user_id'])
    auth_token = create_auth_token(user_id)
    resp = make_response(redirect(config.base_url))
    resp.set_cookie('ball_auth_token', auth_token)
    resp.set_cookie('ball_user_id', user_id)
    return resp


@ball.route('/auth/google/start')
def auth_google_start():
    return redirect(
        'https://accounts.google.com/o/oauth2/v2/auth?' +
        'client_id=' + config.google_client_id +
        '&response_type=code' +
        '&scope=https://www.googleapis.com/auth/plus.login' +
        '&redirect_uri=' + config.base_url + '/auth/google/done')


@ball.route('/auth/google/done')
def auth_google_done():
    try:
        code = request.args.get('code', '')
    except:
        code = 'None'
    google_oauth_base = 'https://www.googleapis.com/oauth2/v4/token'
    google_oauth_data = urllib.parse.urlencode({
        'client_id': config.google_client_id,
        'client_secret': config.google_client_secret,
        'redirect_uri': config.base_url + '/auth/google/done',
        'code': code,
        'grant_type': 'authorization_code'})
    response = urllib.request.urlopen(
        google_oauth_base,
        google_oauth_data.encode('utf-8'))
    res = json.loads(response.read().decode())
    if 'error' in res:
        error_content = 'Failed auth: ' + str(res['error_description'])
        return render_template('template.html',
                               title='Failed auth',
                               base=config.base_url,
                               content=error_content)
    access_token = res['access_token']
    google_login_base = 'https://www.googleapis.com/plus/v1/people/me'
    google_login_data = \
        urllib.parse.urlencode(
            {'access_token': access_token}
        )
    res = json.loads(urllib.request.urlopen(google_login_base + '?' +
                     google_login_data).read().decode())
    user_id = 'google:' + str(res['id'])
    auth_token = create_auth_token(user_id)
    resp = make_response(redirect(config.base_url))
    resp.set_cookie('ball_auth_token', auth_token)
    resp.set_cookie('ball_user_id', user_id)
    return resp

class LoggerHandler (logging.StreamHandler):
    def emit (x, record):
        logging.StreamHandler.emit (x, record)

if __name__ == '__main__':
    webc = config.config['web']
    ball.debug = webc['debug']
    ball.logger.setLevel(logging.DEBUG)
    handler = LoggerHandler()
    handler.setLevel(logging.DEBUG)
    ball.logger.addHandler(handler)
    ball.run(host=webc['host'], port=webc['port'])
