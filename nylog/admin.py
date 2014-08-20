from flask import render_template, flash, redirect, url_for
from .app import app
from .models import db, User, Post, Comment, IntegrityError
from .auth import admin_required
from flask_scrypt import generate_password_hash, generate_random_salt
from wtforms.validators import DataRequired
from wtforms import (StringField, HiddenField, PasswordField, BooleanField,
                     TextAreaField, DateField)
from flask_wtf import Form
from flask.ext.babel import gettext as _, lazy_gettext as _l
from datetime import date as dtdate

@app.route('/admin/')
@admin_required
def admin_home():
    return render_template('admin/index.html')

@app.route('/admin/users')
@admin_required
def admin_users(form = None):
    users = User.query.all()
    if form is None:
        form = NewUserForm()
    return render_template('admin/users.html', users = users, form_new = form,
                           delete_user = FormDeleteUser)

@app.route('/admin/user/create', methods = ['POST'])
@admin_required
def create_user():
    form = NewUserForm()
    if form.validate():
        user = new_user(form.login.data, form.password.data)
        # and save it all
        db.session.add(user)
        try:
            db.session.commit()
            flash(_('Reader %s added !') % user.login)
        except IntegrityError:
            flash(_("Login '%s' already taken") % user.login, 'error')

        return redirect(url_for('admin_users'))
    else:
        return admin_users(form)

def new_user(login, password):
    user = User()
    user.login = login

    # generate a strong cryptographic hash from the password
    salt = generate_random_salt(byte_size = 64)
    phash = generate_password_hash(password, salt,
                                   N=16384, r=8, p=1, buflen=64)
    user.password = phash + salt

    return user

@app.route('/admin/user/delete', methods = ['POST'])
@admin_required
def delete_user():
    form = DeleteForm()
    if form.validate():
        try:
            user_id = int(form.id.data)
            if User.query.filter_by(id = user_id).delete() == 1:
                db.session.commit()
                flash(_('Reader deleted !'))
        except ValueError:
            pass
    return redirect(url_for('admin_users'))

class NewUserForm(Form):
    login = StringField(_l('Login'), validators = [DataRequired()])
    password = PasswordField(_l('Password'), validators = [DataRequired()])

class DeleteForm(Form):
    id = HiddenField(validators = [DataRequired()])

def FormDeleteUser(user):
    "Return a DeleteForm instance with id value set to user.id"
    form = DeleteForm()
    form.id.data = user.id
    return form

@app.route('/admin/post/write')
@admin_required
def write_post():
    return render_template('admin/write_post.html', form = NewPostForm())

@app.route('/admin/post/new', methods = ['POST'])
@admin_required
def new_post():
    form = NewPostForm()
    if form.validate():
        post = Post()
        post.title = form.title.data
        post.slug = form.get_slug()
        post.content = form.content.data
        post.covered_period = form.covered_period.data
        post.covers_week = form.week.data
        
        db.session.add(post)
        db.session.commit()

        flash(_('Entry published !'))
        return redirect(url_for('write_post'))
    return render_template('admin/write_post.html', form = form)

class NewPostForm(Form):
    title = StringField(_l('Title'), validators = [DataRequired()])
    content = TextAreaField(_l('Content'), validators = [DataRequired()])
    covered_period = DateField(_l('Date'), validators = [DataRequired()],
                               default = lambda : dtdate.today())
    week = BooleanField(_l('Covers whole week'))

    def get_slug(self):
        return slugify(self.title.data)

# from http://flask.pocoo.org/snippets/5/
import re
from unicodedata import normalize

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim='-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(str(word))
    return delim.join(result)
