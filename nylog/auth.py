from flask import render_template, request, redirect, url_for, flash
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
from flask_wtf import Form
from wtforms import StringField, PasswordField, HiddenField
from wtforms.validators import DataRequired
from flask_scrypt import check_password_hash
from flask.ext.babel import gettext as _, lazy_gettext as _l
from functools import wraps

from .app import app
from .models import db, User, NoResultFound

login_manager = LoginManager(app)
login_manager.login_view = "ask_login"
login_manager.login_message = _("Please log in to access this part of the log.")

class NYLogUser:
    """User class for flask-login
    cf https://flask-login.readthedocs.org/en/latest/#your-user-class
    """

    def __init__(self, user):
        self.user = user

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.user.login

    @property
    def id(self):
        return self.user.id

    @property
    def login(self):
        return self.user.login

    @property
    def is_admin(self):
        return self.login == app.config['NYLOG_ADMIN']

    def check_password(self, password):
        # hash stored in the database = scrypt hash (88 chars) + salt (88 chars)
        hash = self.user.password[:88]
        salt = self.user.password[88:]
        if isinstance(hash, str):
            hash = hash.encode('utf-8')
        return check_password_hash(password, hash, salt,
                                   N=16384, r=8, p=1, buflen=64)

def admin_required(f):
    "Decorate a view with this function to restrict the access to the log admin"
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            return render_template('admin_only.html'), 403
    return wrapper

@login_manager.user_loader
def load_user(login):
    "Called by flask-login when it loads the user from the session cookie"
    return get_user(login)

def get_user(login):
    "Return a NYLogUser for the given login or None if no such user exists"
    try:
        u = User.query.filter_by(login = login).one()
        return NYLogUser(u)
    except NoResultFound:
        return None

@app.route('/login', methods=['GET'])
def ask_login():
    form = LoginForm()
    form.next.data = request.args.get('next')
    return render_template('login.html', form = form)

@app.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = load_user(form.login.data)
        if user is None:
            flash(_("This login is unknown."))
        elif user.check_password(form.password.data):
            login_user(user, remember = True)
            flash(_('You are now connected as %s') % user.login)
            return redirect(form.next.data or url_for('index'))
        else:
            flash(_("Login and password didn't match."))
    return redirect(url_for('ask_login', next = form.next.data))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

class LoginForm(Form):
    login = StringField(_l('Login'), validators=[DataRequired()])
    password = PasswordField(_l('Password'))
    next = HiddenField()
