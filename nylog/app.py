from flask import Flask, render_template
from flask.ext.babel import Babel
import arrow

app = Flask('nylog')

app.config.from_envvar('NYLOG_CONFIG')

babel = Babel(app)

@app.errorhandler(404)
def handler_page_not_found(e):
    return render_template("404.html"), 404

@app.template_filter()
def format_date_local(date):
    "Human friendly datetime display"
    adate = arrow.get(date)
    locale = 'en_us'

    diff = arrow.utcnow() - adate    
    if diff.days <= 2:
        return adate.humanize(locale = locale)
    else:
        return adate.format('DD MMMM YYYY, HH:mm', locale = locale)

# from http://flask.pocoo.org/snippets/28/
import re
from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
@evalcontextfilter
def paragraphs(eval_ctx, value):
    "Replace newlines by html <br/> tags and divides the text into <p>(aragraphs)"
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result
