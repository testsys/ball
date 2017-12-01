
from flask import render_template_string
import cgi

import lang


def __wrap(s, raw=[]):
    return lambda **kwargs: render_template_string(
        s,
        **{k: (v if k in raw else cgi.escape(v)) for k, v in kwargs.items()}
    )


link = __wrap('<a href="{{url}}">{{label}}</a>\n')
text = __wrap('{{text}}\n')
event_link = __wrap('<div><a href="{{url}}">{{name}}</a></div>\n')
event_nolink = __wrap('<div><span>{{name}}</span></div>\n')
event_add_form = __wrap(
    '<div><form action="action{{token}}" method="POST">' +
    '<input type="text" placeholder="' +
    lang.lang['index_monitor_url'] + '" name="url" />' +
    '<input type="submit" value="' +
    lang.lang['index_add_event'] + '" />' +
    '</form></div>\n'
)
error = __wrap(
    '<h2 style="color: red;">{{message}}</h2>\n'
    '<p><a href="{{back}}">' + lang.lang['back'] + '</a></p>\n'
)
action_link = __wrap(
    '<form action="action{{token}}" id="form{{token}}" method="POST">' +
       '<span class="link" onclick="document.getElementById(\'form{{token}}\').submit();">' +
       '{{label}}</span>' +
    '</form>'
)
action_link_raw = __wrap(
    '<form action="action{{token}}" id="form{{token}}" method="POST">' +
       '<span class="link" onclick="document.getElementById(\'form{{token}}\').submit();">' +
       '{{label}}</span>' +
    '</form>',
    raw={'label'}
)
problem_header = __wrap('<h2>{{letter}}: {{name}}</h2>\n')
problem_color = __wrap(
    '<div><span style="color:{{color}}">' +
    lang.lang['problem_cur_color'] +
    ' <b>{{color}}</b></span></div>\n'
)
color_select = __wrap(
    '<div>{{link}}</div>\n',
    raw={'link'}
)
color_select_label = __wrap(
    '<span style="color:{{color}}">' + lang.lang['problem_set_color'] +
    ' <b>{{color}}</b></span>'
)
monitor_link = __wrap(
    '<div><a href="{{url}}">' +
    lang.lang['event_header_monitor_link'] + '</a></div>\n'
)
problems = __wrap(
    '<h2>' + lang.lang['event_header_problems'] + '</h2>\n' +
    '<table style="width: 100%;"><tr>' +
    '{{problems}}' +
    '</tr></table>\n',
    raw={'problems'}
)
problem = __wrap(
    '<td class="balloons_problem_color" style="' +
    'background-color: {{color}};">{{color_token}}</td>\n' +
    '<td class="balloons_problem_letter">' +
    '<a href="{{url}}">{{letter}}</a>({{count}})</td>\n',
    raw={'color_token'}
)
fts = __wrap('<b>' + lang.lang['event_queue_first_solved'] + '</b> {{text}}')
fts_no = __wrap('{{text}}')
balloon = __wrap(
    '<tr class="balloons_row">'
    '<td class="balloons_balloon_color"' +
    ' style="background-color: {{color}}">{{color_token}}</td>' +
    '<td>{{problem_comment}} <b>{{letter}}</b></td>' +
    '<td>{{team_comment}} <b>{{team_short}}</b>: {{team}}</td>' +
    '<td>{{state}}</td>' +
    '<tr>\n',
    raw={'color_token', 'problem_comment', 'team_comment', 'state'}
)
balloons = __wrap(
    '<h2>{{header}}</h2>\n' +
    '<table style="width: 100%;">\n' +
    '{{balloons}}' +
    '</table>\n',
    raw={'balloons'}
)
auth = __wrap(
    '<div>' + lang.lang['index_not_authorised'] +
    ' <a href="{{url}}">' +
    lang.lang['index_log_in'] +
    '</a></div>\n'
)
auth_ok = __wrap('<div><b>{{user}}</b></div>\n')
auth_link = __wrap('<div><a href="{{url}}">{{label}}</a></div>\n')
volunteer = __wrap(' ({{id}})')

