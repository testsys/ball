#!/usr/bin/env python3

from flask import Flask, abort, render_template, request, make_response, redirect
import json, urllib
import logging

from miscellaneous import *
import auth
import lang
import design
import config
from balloon import Balloon
from db import DB

ball = Flask(__name__)
actions = {}


def page(*, title, content):
    return render_template(
        'template.html',
        title=title,
        base=config.base_url,
        content=content
    )

def make_url(suffix=""):
    return config.base_url + "/" + suffix


# actions: methods that modify something

@arguments(None, id=int)
def action_access_grant(db, *, id):
    db.volunteer_access(id, True)
    return redirect(make_url('volunteers'))

@arguments(None, id=int)
def action_access_refuse(db, *, id):
    db.volunteer_access(id, False)
    return redirect(make_url('volunteers'))

@arguments(None, url=str)
def action_event_add(db, *, url):
    db.event_add(1, url)
    return redirect(config.base_url)

@arguments(None, problem=int, value=str)
def action_color_set(db, *, problem, value):
    db.problem_color(problem, value)
    return redirect(make_url("problem%d" % problem))

@arguments(None, event=int, balloon=int, volunteer=str)
def action_balloon_done(db, *, event, balloon, volunteer):
    db.balloon_done(balloon, volunteer)
    return redirect(make_url("event%d" % event))

@arguments(None, event=int, balllon=int)
def action_balloon_drop(db, *, event, balloon):
    db.balloon_drop(balloon)
    return redirect(make_url("event%d" % event))

@arguments(None, event=int, balloon=int, volunteer=str)
def action_balloon_take(db, *, event, balloon, volunteer):
    balloon = db.balloon(balloon, lock=True)
    if balloon is None:
        return abort(404)
    state = int (balloon[4])
    if state >= 100:
        return page(
            title=lang.lang['error'],
            content=design.error(
                message=lang.lang['error_ball_taken'],
                back=make_url("event%d" % event)
            )
        )
    db.balloon_take(balloon, volunteer)
    return redirect(make_url("event%d" % event))


@ball.route('/action_mk2', methods=['POST'])
def do_action_mk2():
    user_id, auth_html, user_ok = check_auth(request)
    if not user_ok:
        return redirect(config.base_url, code=307)
    token = request.form['token']
    token_cookie = request.cookies.get('ball_token')
    if token != token_cookie or len(token) < 10:
        print ("token mismatch: %s vs %s" % (repr (token), repr (token_cookie)))
        return abort(403);
    try:
        callback = {
            'access_grant': action_access_grant,
            'access_refuse': action_access_refuse,
            'event_add': action_event_add,
            'color_set': action_color_set,
            'balloon_take': action_balloon_take,
            'balloon_drop': action_balloon_drop,
            'balloon_done': action_balloon_done,
        }[request.form['method']]
    except KeyError:
        print ("unknown action method: '%s'" % request.form['method'])
        return abort(404)
    db = DB()
    result = callback(db, **{
        k: v for k, v in request.form.items()
        if k not in ['method', 'token']
    })
    db.close(commit=True)
    return result


volunteer_cache = {}
def volunteer_get(volunteer_id):
    if volunteer_id in volunteer_cache:
        return volunteer_cache[volunteer_id]
    if volunteer_id.startswith('vk:'):
        vk_id = int (volunteer_id[3:])
        api_url = "https://api.vk.com/method/users.get?user_ids=%d" % vk_id
        res = json.loads(urllib.request.urlopen(api_url).read().decode())
        if 'error' in res:
            return None
        res = res['response'][0]
        volunteer_cache[volunteer_id] = (
            "%s %s" % (res['first_name'], res['last_name']),
            "https://vk.com/id%s" % res['uid']
        )
        return volunteer_cache[volunteer_id]
    return None


@ball.route('/')
def index():
    user_id, auth_html, user_ok = check_auth(request)
    content = ''
    db = DB()
    events = db.events()
    db.close()
    if len(events) == 0:
        content = lang.lang['index_no_events']
    if user_ok:
        event_link = design.event_link
    else:
        event_link = design.event_nolink
    for e in events:
        if e[1]:
            content += event_link(url=config.base_url + '/event' + str(e[0]), name=e[1])
        else:
            content += design.event_nolink(name=e[3])
    if user_ok:
        content += design.action_form_event(arguments={
            'method': 'event_add',
        })
        content += design.link(url=config.base_url + '/volunteers', label=lang.lang['access_manage'])
    return render_template(
        'template.html',
        title=lang.lang['index_title'],
        auth=auth_html,
        base=config.base_url,
        content=content
    )


@ball.route('/volunteers')
def volunteers():
    user_id, auth_html, user_ok = check_auth(request)
    if not user_ok:
        return redirect(config.base_url)
    volunteers = []
    for id in config.allowed_users:
        volunteer = volunteer_get(id)
        if volunteer is None:
            volunteer_str = design.volunteer(id=str(id))
        else:
            volunteer_name, volunteer_link = volunteer
            volunteer_str = ' ' + design.volunteer_ext(
                name=volunteer_name,
                url=volunteer_link
            )
        if id == user_id:
            change = design.text(text=lang.lang['this_is_you'])
        else:
            change = design.text(text=lang.lang['volunteer_from_config'])
        volunteers.append(design.volunteer_access(
            name=volunteer_str,
            change=change
        ))
    db = DB()
    for db_id, id, access in db.volunteers():
        volunteer = volunteer_get(id)
        if volunteer is None:
            volunteer_str = design.volunteer(id=str(id))
        else:
            volunteer_name, volunteer_link = volunteer
            volunteer_str = ' ' + design.volunteer_ext(
                name=volunteer_name,
                url=volunteer_link
            )
        if id == user_id:
            change = design.text(text=lang.lang['this_is_you'])
        elif access:
            change = design.action_link_mk2(
                arguments={
                    'method': 'access_refuse',
                    'id': db_id
                },
                label=lang.lang['access_refuse']
            )
        else:
            change = design.action_link_mk2(
                arguments={
                    'method': 'access_grant',
                    'id': db_id
                },
                label=lang.lang['access_grant']
            )
        volunteers.append((
            design.volunteer_access if access else design.volunteer_noaccess
        )(
            name=volunteer_str,
            change=change
        ))
    db.close()
    volunteers = ''.join(volunteers)
    content = design.volunteers(volunteers=volunteers)
    response = make_response (render_template(
        'template.html',
        title=lang.lang['volunteers_title'],
        auth=auth_html,
        base=config.base_url,
        content=content
    ))
    token = auth.create_token(user_id, add_random=True)
    response.set_cookie('ball_token', token)
    return response


@ball.route('/problem<int:problem_id>')
def problem(problem_id):
    user_id, auth_html, user_ok = check_auth(request)
    if not user_ok:
        return redirect(config.base_url)
    problem_id = int(problem_id)
    content = ''
    db = DB()
    problems = [db.problem(problem_id)]
    db.close()
    problems_html = design.problem_header(letter=problems[0]['letter'], name=problems[0]['name'])
    content += problems_html
    colors_html = ''
    colors_html += design.problem_color(color=problems[0]['color'])
    colors_html += design.action_form_color(
        arguments={
            'method': 'color_set',
            'problem': problem_id
        },
        default=problems[0]['color']
    )
    content += colors_html
    response = make_response (render_template(
        'template.html',
        title=problems[0]['letter'],
        auth=auth_html,
        base=config.base_url,
        content=content
    ))
    token = auth.create_token(user_id, add_random=True)
    response.set_cookie('ball_token', token)
    return response


def get_state_str_current(event_id, b, *, user_id):
    state_str = design.action_link_mk2(
        arguments={
            'method': 'balloon_done',
            'event': event_id,
            'balloon': b.id,
            'volunteer': user_id
        },
        label=lang.lang['event_queue_done']
    ) + ' ' + design.action_link_mk2(
        arguments={
            'method': 'balloon_drop',
            'event': event_id,
            'balloon': b.id
        },
        label=lang.lang['event_queue_drop']
    )
    return state_str


def get_state_str_queue(event_id, b, *, user_id):
    state_str = None
    if b.state >= 0 and b.state < 100:
        state_str = (
            design.text(text=lang.lang['balloon_state_wanted']) + ' ' +
            design.action_link_mk2(
                arguments={
                    'method': 'balloon_take',
                    'event': event_id,
                    'balloon': b.id,
                    'volunteer': user_id
                },
                label=lang.lang['event_queue_take']
            )
        )
    elif b.state < 200:
        state_str = design.text(text=lang.lang['balloon_state_carrying'])
    elif b.state < 300:
        state_str = design.text(text=lang.lang['balloon_state_delivered'])
    else:
        state_str = design.text(lang.lang['balloon_state_error'])
    if str(b.volunteer_id) != '':
        volunteer = volunteer_get (str(b.volunteer_id))
        if volunteer is None:
            state_str += ' ' + design.volunteer(id=str(b.volunteer_id))
        else:
            volunteer_name, volunteer_link = volunteer
            state_str += ' ' + design.volunteer_ext(
                name=volunteer_name,
                url=volunteer_link
            )
    return state_str


@ball.route('/event<int:event_id>')
def event(event_id):
    user_id, auth_html, user_ok = check_auth(request)
    if not user_ok:
        return redirect(config.base_url)
    event_id = int(event_id)
    content = ''
    db = DB()
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
    event_html += design.standings_link(url=make_url("event%d/standings" % event_id))
    content += event_html

    problems = db.problems(event_id)
    problems_map = {p['id']: i for i, p in enumerate (problems)}
    for p in problems:
        cnt = db.balloons_count(event_id, p['id'])
        p['cnt'] = cnt
    problems_html = design.problems(
        problems=''.join ([
            design.problem(
                color_token='&nbsp;' if p['color'] else '?',
                color=p['color'],
                url=config.base_url + '/problem' + str(p['id']),
                letter=p['letter'],
                count=str(p['cnt'])
            )
            for p in problems
        ])
    )
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
        nonlocal user_id
        if len(balloons) == 0:
            return ''
        balloons_html = []
        for b in balloons:
            p = problems[problems_map[b.problem_id]]
            t = teams[teams_map[b.team_id]]
            state_str = get_state_str(event_id, b, user_id=user_id)
            balloons_text = '&nbsp;'
            if not p['color']:
                balloons_text = '?'
            if first_to_solve[b.problem_id] == b.id:
                x = design.fts(text=lang.lang['event_queue_problem'])
            else:
                x = design.fts_no(text=lang.lang['event_queue_problem'])
            # FTS for team is confusing, disable it for now
            #if b.team_id in first_solved and first_solved[b.team_id] == b.id:
            #    y = design.fts(text=lang.lang['event_queue_team'])
            #else:
            y = design.fts_no(text=lang.lang['event_queue_team'])
            balloons_html.append(design.balloon(
                color_token=balloons_text,
                color=p['color'],
                problem_comment=x,
                letter=p['letter'],
                team_comment=y,
                team_short=t['name'],
                team=t['long_name'],
                state=state_str
            ))
        balloons_html = design.table(
            header=header + " (%d)" % len (balloons),
            content=''.join (balloons_html)
        )
        return balloons_html

    balloons = db.balloons_my(event_id, user_id)
    balloons = list (map (Balloon, balloons))
    content += get_balloons_html(
        lang.lang['event_header_your_queue'],
        get_state_str_current, balloons
    )
    balloons = db.balloons_new(event_id)
    balloons = list (map (Balloon, reversed (balloons)))
    content += get_balloons_html(
        lang.lang['event_header_offer'],
        get_state_str_queue, balloons
    )
    balloons = db.balloons_old(event_id)
    balloons = list (map (Balloon, balloons))
    content += get_balloons_html(
        lang.lang['event_header_queue'],
        get_state_str_queue, balloons
    )

    db.close()
    return render_template(
        'template.html',
        title=event['name'],
        base=config.base_url,
        content=content)


@ball.route('/event<int:event_id>/standings')
def event_standings(event_id):
    user_id, auth_html, user_ok = check_auth(request)
    if not user_ok:
        return redirect(config.base_url)
    event_id = int(event_id)
    db = DB()
    try:
        e = db.event(event_id)
    except KeyError:
        return redirect(config.base_url)
    event = {
        'name': e[1],
        'state': e[2],
        'url': e[3]
    }
    problems_header = []
    problems = db.problems(event_id)
    for p in problems:
        problems_header.append(design.standings_problem(
            name_full=p['name'],
            name_short=p['letter']
        ))
        try:
            p['fts'] = db.fts(event_id, problem_id=p['id'])
        except KeyError:
            pass

    oks = {}
    for b in db.balloons(event_id):
        oks[(b['team_id'], b['problem_id'])] = (b['id'], b['time_local'])

    standings_header = ''.join(problems_header)
    teams = []
    for t in db.teams(event_id):
        score = 0
        penalty = 0
        team_row = []
        for p in problems:
            key = (t['id'], p['id'])
            print (key, oks.get(key, None))
            if key in oks:
                ok_id, time = oks[key]
                team_row.append(design.standings_yes(
                    time=int(time),
                    fts=ok_id == p['fts']
                ))
                score += 1
                penalty += int(time / 60) # TODO: incorrect: does not assume previous attempts
            else:
                team_row.append(design.standings_nope())
        teams.append ([t['long_name'], ''.join(team_row), score, penalty, True, False])

    teams = list(sorted(teams, key=lambda t: (-t[2], t[3])))
    for i in range(1, len(teams)):
        teams[i][4] = not teams[i - 1][4]
    for i in range(len(teams) - 2, -1, -1):
        if teams[i][2] == teams[i + 1][2]:
            teams[i][5] = teams[i + 1][5]
        else:
            teams[i][5] = not teams[i + 1][5]

    teams_list = []
    for name, problems, score, penalty, even, block_even in teams:
        teams_list.append(design.standings_team(
            row=even,
            block=block_even,
            name=name,
            problems=problems,
            rank=1,
            score=score,
            penalty=penalty
        ))
        even = not even
    standings_body = ''.join(teams_list)
    content = design.warning(
        message=lang.lang['warning_no_penalty_attempts']
    ) + design.standings_table(
        header=standings_header,
        body=standings_body
    )
    db.close()
    return page(
        title=event['name'],
        content=content
    )


user_cache = {}
def check_auth(request):
    auth_html = design.auth(url=config.base_url + 'auth')
    try:
        user_id = request.cookies.get('ball_user_id')
        auth_token = request.cookies.get('ball_auth_token')
    except:
        return None, auth_html, False
    if not auth.check(user_id, auth_token):
        return None, auth_html, False
    #  need to invalidate cache in action_access_*
    # if user_id in user_cache:
    #     return user_cache[user_id]
    auth_html = design.auth_ok(user=str(user_id))
    user_ok = user_id in config.allowed_users
    if not user_ok:
        db = DB()
        user_ok = db.volunteer_get(user_id)
        db.close(commit=True)
    user_cache[user_id] = user_id, auth_html, user_ok
    return user_cache[user_id]


@ball.route('/auth')
def method_auth():
    user_id, auth_html, user_ok= check_auth(request)
    content = design.auth_link(url=config.base_url + '/auth/vk/start', label='VK') + \
        design.auth_link(url=config.base_url + '/auth/google/start', label='Google')
    return render_template(
        'template.html',
        title=lang.lang['auth'],
        auth=auth_html,
        base=config.base_url,
        content=content)


@ball.route('/auth/vk/start')
def auth_vk_start():
    return redirect(auth.vk.url)


@ball.route('/auth/vk/done')
def auth_vk_done():
    try:
        code = request.args.get('code', '')
    except:
        code = 'None'
    try:
        user_id = auth.vk.do (code)
    except auth.AuthentificationError as error:
        error_content = 'Failed auth: ' + str(error)
        return render_template(
            'template.html',
            title='Failed auth',
            base=config.base_url,
            content=error_content)
    auth_token = auth.create_token(user_id)
    resp = make_response(redirect(config.base_url))
    resp.set_cookie('ball_auth_token', auth_token)
    resp.set_cookie('ball_user_id', user_id)
    return resp


@ball.route('/auth/google/start')
def auth_google_start():
    return redirect(auth.google.url)


@ball.route('/auth/google/done')
def auth_google_done():
    try:
        code = request.args.get('code', '')
    except:
        code = 'None'
    try:
        user_id = auth.google.do(code)
    except auth.AuthentificationError as error:
        error_content = 'Failed auth: ' + str(error)
        return render_template('template.html',
                               title='Failed auth',
                               base=config.base_url,
                               content=error_content)
    auth_token = auth.create_token(user_id)
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


