
from flask import render_template_string
from html import escape

from miscellaneous import *
import lang


# def __wrap(s, raw=[]):
#    return lambda **kwargs: render_template_string(
#        s,
#        **{k: (v if k in raw else escape(v)) for k, v in kwargs.items()}
#    )


def link(*, url, label):
    url = escape(url)
    label = escape(label)
    return '<a href="%s">%s</a>\n' % (url, label)

def text(*, text):
    text = escape(text)
    return text + "\n"

def event_link(*, url, name):
    url = escape(url)
    name = escape(name)
    return '<div><a href="%s">%s</a></div>\n' % (url, name)

def event_nolink(*, url=None, name):
    # url is ignored
    name = escape(name)
    return '<div><span>%s</span></div>\n' % name

@arguments(message=escape)
def warning(*, message):
    return '<h2 style="color: red;">%s</h2>\n' % message

def error(*, message, back):
    message = escape(message)
    back = escape(back)
    return (
        '<h2 style="color: red;">%s</h2>\n'
        '<p><a href="%s">' + lang.lang['back'] + '</a></p>\n'
    ) % (message, back)

form_id = 0
def action_link_mk2(*, arguments, label, raw=False):
    global form_id
    if not raw:
        label = escape(label)
    form_id += 1
    return (
        '<form action="action_mk2" id="form%d" method="POST">' +
            '<input type="hidden" name="token" value="" />' +
            '%s' +
            '<span class="link" onclick="balloon_submit_form(\'form%d\');">%s</span>' +
        '</form>'
    ) % (
        form_id,
        ''.join([
            '<input type="hidden" name="%s" value="%s" />' % (escape(str(k)), escape(str(v)))
            for k, v in arguments.items()
        ]),
        form_id,
        label
    )

def action_form_event(*, arguments):
    global form_id
    form_id += 1
    return (
        '<div><form action="action_mk2" id="form%d" method="POST">\n' +
            '<input type="hidden" name="token" value="" />\n' +
            '%s' +
            '<input type="text" placeholder="' +
                lang.lang['index_monitor_url'] + '" name="url" />' +
            '<input type="button" onclick="balloon_submit_form(\'form%d\');" value="%s" />\n' +
        '</form></div>\n'
    ) % (
        form_id,
        ''.join([
            '<input type="hidden" name="%s" value="%s" />\n' % (escape(str(k)), escape(str(v)))
            for k, v in arguments.items()
        ]),
        form_id,
        lang.lang['index_add_event']
    )

def action_form_color(*, arguments, default):
    global form_id
    form_id += 1
    return (
        '<form action="action_mk2" id="form%d" method="POST">\n' +
            '<input type="hidden" name="token" value="" />\n' +
            '%s' +
            '<span>%s</span>\n' +
            '<input type="color" name="value" value="%s" />\n' +
            '<span class="link" onclick="balloon_submit_form(\'form%d\');">%s</span>\n' +
        '</form>\n'
    ) % (
        form_id,
        ''.join([
            '<input type="hidden" name="%s" value="%s" />\n' % (escape(str(k)), escape(str(v)))
            for k, v in arguments.items()
        ]),
        lang.lang['color_set_new'],
        default,
        form_id,
        lang.lang['color_set_commit']
    )

def action_link_raw(*, token, label):
    token = escape(token)
    return (
        '<form action="action%s" id="form%s" method="POST">' +
            '<span class="link" onclick="document.getElementById(\'form%s\').submit();">' +
            '%s</span>' +
        '</form>'
    ) % (token, token, token, label)

def problem_header(*, letter, name):
    letter = escape(letter)
    return '<h2>%s: %s</h2>\n' % (letter, name)

def problem_color(*, color):
    color = escape(color)
    return (
        '<div><span style="color:%s">' +
        lang.lang['problem_cur_color'] +
        ' <b>%s</b></span></div>\n'
    ) % (color, color)

def color_select(*, link):
    return '<div>%s</div>\n' % link

def color_select_label(*, color):
    color = escape(color)
    return (
        '<span style="color:%s">' + lang.lang['problem_set_color'] +
        ' <b>%s</b></span>'
    ) % (color, color)

def standings_link(*, url):
    url = escape(url)
    return (
        '<div><a href="%s">' +
        lang.lang['event_header_monitor_link'] + '</a></div>\n'
    ) % url

@arguments(name_full=escape, name_short=escape)
def standings_problem(*, name_full, name_short):
    return (
        '<th class="pcms pcms_problem" title="%s">%s</th>'
    ) % (name_full, name_short)

def standings_nope():
    return '<td class="pcms">.</td>'

@arguments(time=int, fts=bool)
def standings_yes(*, time, fts):
    return (
        '<td class="pcms"><i class="pcms%s">+<s class="pcms"><br />%02d:%02d</s></i></td>'
    ) % (
        ' pcms_fts' if fts else '',
        time // 60, time % 60
    )

@arguments(name=escape, row=bool, block=bool, problems=None, rank=int, score=int, penalty=int)
def standings_team(*, row, block, name, problems, rank, score, penalty):
    return (
        '<tr class="pcms_row%d%d">'+
        '<td class="pcms pcms_rankl">%d</td>' +
        '<td class="pcms pcms_party">%s</td>'
        '%s' +
        '<td class="pcms">%d</td>' +
        '<td class="pcms pcms_penalty">%d</td>' +
        '</tr>'
    ) % (
        1 if block else 0,
        1 if row else 0,
        rank, name, problems, score, penalty
    )

def standings_table(*, header, body):
    return (
        '<table class="pcms_standings"><thead><tr>' +
        '<th class="pcms pcms_rankl">' + lang.lang['standings_rank'] + '</th>' +
        '<th class="pcms pcms_party">' + lang.lang['standings_team'] + '</th>' +
        '%s' +
        '<th class="pcms pcms_solved">' + lang.lang['standings_solved'] + '</th>' +
        '<th class="pcms pcms_penalty">' + lang.lang['standings_penalty'] + '</th>' +
        '</tr></thead><tbody>' +
        '%s' +
        '</tbody></table>'
    ) % (header, body)

def problem(*, color, color_token, url, letter, count):
    color = escape(color)
    letter = escape(letter)
    url = escape(url)
    count = escape(count)
    return (
        '<td class="balloons_problem_color" style="' +
        'background-color: %s;">%s</td>\n' +
        '<td class="balloons_problem_letter">' +
        '<a href="%s">%s</a>(%s)</td>\n'
    ) % (color, color_token, url, letter, count)

def fts(*, text):
    text = escape(text)
    return ('<b>' + lang.lang['event_queue_first_solved'] + '</b> %s ') % text

def fts_no(*, text):
    text = escape(text)
    return "%s " % text

def balloon(*, color, color_token, problem_comment, letter, team_comment, team_short, team, state):
    color = escape(color)
    letter = escape(letter)
    team_short = escape(team_short)
    team = escape(team)
    return (
        '<tr class="balloons_row">' +
        '<td class="balloons_balloon_color"' +
        ' style="background-color: %s">%s</td>' +
        '<td>%s <b>%s</b></td>' +
        '<td>%s <b>%s</b>: <span style="color: gray;">%s</span></td>' +
        '<td>%s</td>' +
        '</tr>\n'
    ) % (color, color_token, problem_comment, letter, team_comment, team_short, team, state)

def volunteer_access(*, name, change):
    return (
        '<tr>' +
        '<td>%s</td>' +
        '<td style="color: green; size: 8pt;">' + lang.lang['access_yes'] + '</td>' +
        '<td>%s</td>' +
        '</tr>\n'
    ) % (name, change)

def volunteer_noaccess(*, name, change):
    return (
        '<tr>' +
        '<td>%s</td>' +
        '<td style="color: red; size: 8pt;">' + lang.lang['access_no'] + '</td>' +
        '<td>%s</td>' +
        '</tr>\n'
    ) % (name, change)

def table(*, header, content):
    header = escape(header)
    return (
        '<h2>%s</h2>\n' +
        '<table style="width: 100%%;">\n' +
        '%s' +
        '</table>\n'
    ) % (header, content)

def problems(*, problems):
    return (
        '<h2>' + lang.lang['event_header_problems'] + '</h2>\n' +
        '<table style="width: 100%%;"><tr>' +
        '%s' +
        '</tr></table>\n'
    ) % problems

def volunteers(*, volunteers):
    return table(content=volunteers, header=lang.lang['header_volunteers'])

def auth(*, url):
    url = escape(url)
    return (
        '<div>' + lang.lang['index_not_authorised'] +
        ' <a href="%s">' +
        lang.lang['index_log_in'] +
        '</a></div>\n'
    ) % url

def auth_ok(*, user):
    user = escape(user)
    return '<div><b>%s</b></div>\n' % user

def auth_link(*, url, label):
    url = escape(url)
    label = escape(label)
    return '<div><a href="%s">%s</a></div>\n' % (url, label)

def volunteer(*, id):
    id = escape(id)
    return ' (%s)' % id

def volunteer_ext(*, name, url):
    name = escape(name)
    url = escape(url)
    return ' (<a href="%s">%s</a>)' % (url, name)

