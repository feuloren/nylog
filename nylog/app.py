from flask import Flask, render_template, request
from flask.ext.babel import Babel, format_datetime
import arrow

class NYLogApp(Flask):
    def post(self, rule, **options):
        def decorator(f):
            options['methods'] = ['POST']
            self.add_url_rule(rule, None, f, **options)
            return f
        return decorator

app = NYLogApp('nylog')

app.config.update(
    NYLOG_ADMIN = 'admin',
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/nylog.db'
    )
if not(app.config.from_envvar('NYLOG_CONFIG', True)):
    from sys import stderr
    print("Warning : no config loaded, set the environment variable NYLOG_CONFIG to point the file storing the config",
          file = stderr)

babel = Babel(app)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['fr', 'en'])

@app.errorhandler(404)
def handler_page_not_found(e):
    return render_template("404.html"), 404

@app.template_filter()
def format_date_local(date):
    "Human friendly datetime display"
    adate = arrow.get(date)
    locale = get_locale()

    diff = arrow.utcnow() - adate    
    if diff.days <= 2:
        return adate.humanize(locale = locale)
    else:
        return format_datetime(date)

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
