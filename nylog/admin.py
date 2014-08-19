from flask import render_template, flash, redirect, url_for
from .app import app
from .models import db, User, Post, Comment, IntegrityError
from .auth import admin_required
from flask_scrypt import generate_password_hash, generate_random_salt
from wtforms.validators import DataRequired
from wtforms import StringField, HiddenField, PasswordField
from flask_wtf import Form
from gettext import gettext as _

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
    login = StringField(_('Login'), validators = [DataRequired()])
    password = PasswordField(_('Password'), validators = [DataRequired()])

class DeleteForm(Form):
    id = HiddenField(validators = [DataRequired()])

def FormDeleteUser(user):
    "Return a DeleteForm instance with id value set to user.id"
    form = DeleteForm()
    form.id.data = user.id
    return form
