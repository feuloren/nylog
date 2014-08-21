from flask import render_template, flash, redirect, url_for
from .app import app
from .models import db, User, Post, Comment, Category, IntegrityError
from sqlalchemy.orm import class_mapper
from .auth import admin_required
from flask_scrypt import generate_password_hash, generate_random_salt
from wtforms.validators import DataRequired
from wtforms import (StringField, HiddenField, PasswordField, BooleanField,
                     TextAreaField, DateField, SelectMultipleField)
from wtforms.widgets import ListWidget, CheckboxInput
from flask_wtf import Form
from flask.ext.babel import gettext as _, lazy_gettext as _l
from datetime import date as dtdate

def class_get_pk(cls):
    "Get the primary key column for cls"
    pks = class_mapper(cls).primary_key
    if len(pks) > 1:
        raise NotImplementedError("Can't use objects with composite primary key")

    return pks[0]


class DeleteForm(Form):
    "A form to delete an sqlalchemy object with a single primary key"
    id = HiddenField(validators = [DataRequired()])

    @classmethod
    def validate_and_delete_for(self_cls, cls):
        """Validate the form and delete the target object
        Does not commit the session
        Return True if object was deleted, False otherwise
        """
        pk = class_get_pk(cls)

        form = self_cls()
        if form.validate_on_submit():
            delid = pk.type.python_type(form.id.data) # Convert from string to Column type
            obj = cls.query.get(delid)
            if not(obj is None):
                db.session.delete(obj)
                return True

        return False

    @classmethod
    def for_class(self_cls, cls):
        "Return a pre-filled form constructor for the class `cls`"
        pk = class_get_pk(cls)

        def fill_form(obj):
            "Instanciate a delete form with primary key value pre-filled from obj"
            if not(isinstance(obj, cls)):
                raise ValueError('Expected object of type %s but got %s' % (repr(cls), repr(obj)))

            form = self_cls()
            form.id.data = str(getattr(obj, pk.name))
            return form

        return fill_form


class ClassChoices:
    def __init__(self, query, label, cls = None):
        """
        :param query : an SQLAlchemy Query to retrieve the choices
        :param repr : a string representing the attribute containing the label
                      or a callable accepting an item as first argument and returning a string
        :param cls : class of the items, if None will be deduced from query
        """

        self.query = query

        if cls is None:
            try:
                cls = query._entities[0].type
            except Exception as e:
                raise ValueError('Could not determine the class from query, please use the cls parameter') from e
        self.pk = class_get_pk(cls).name

        if isinstance(label, str):
            self.repr = lambda x : getattr(x, label)
        elif hasattr(label, '__call__'):
            self.repr = labem
        else:
            raise ValueError('repr should be a string or a callable')

    def __iter__(self):
        for user in self.query:
            yield (getattr(user, self.pk), self.repr(user))


# Home
@app.route('/admin/')
@admin_required
def admin_home():
    return render_template('admin/index.html')

# Users
class NewUserForm(Form):
    login = StringField(_l('Login'), validators = [DataRequired()])
    password = PasswordField(_l('Password'), validators = [DataRequired()])

def new_user(login, password):
    user = User()
    user.login = login

    # generate a strong cryptographic hash from the password
    salt = generate_random_salt(byte_size = 64)
    phash = generate_password_hash(password, salt,
                                   N=16384, r=8, p=1, buflen=64)
    user.password = phash + salt

    return user

@app.route('/admin/users')
@admin_required
def admin_users(form = None):
    users = User.query.all()
    if form is None:
        form = NewUserForm()
    return render_template('admin/users.html', users = users, form_new = form,
                           delete_user = DeleteForm.for_class(User))

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
            flash(_('Reader %(login)s added !', login = user.login))
        except IntegrityError:
            flash(_("Login '%(login)s' already taken", login = user.login), 'error')

        return redirect(url_for('admin_users'))
    else:
        return admin_users(form)

@app.route('/admin/user/delete', methods = ['POST'])
@admin_required
def delete_user():
    if DeleteForm.validate_and_delete_for(User):
        db.session.commit()
        flash(_('Reader deleted !'))
    return redirect(url_for('admin_users'))


# Posts

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
            result.append(word.decode('utf-8'))
    return delim.join(result)

class NewPostForm(Form):
    title = StringField(_l('Title'), validators = [DataRequired()])
    content = TextAreaField(_l('Content'), validators = [DataRequired()])
    covered_period = DateField(_l('Date'), validators = [DataRequired()],
                               default = lambda : dtdate.today())
    week = BooleanField(_l('Covers whole week'))
    categories = SelectMultipleField(_('Categories'),
                                     widget = ListWidget(),
                                     option_widget = CheckboxInput(),
                                     choices = ClassChoices(Category.query.order_by('name'), 'name'))

    def get_slug(self):
        return slugify(self.title.data)

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
        post.categories.extend(Category.query.filter(Category.name.in_(form.categories.data)))
        
        db.session.add(post)
        db.session.commit()

        flash(_('Entry published !'))
        return redirect(url_for('write_post'))
    return render_template('admin/write_post.html', form = form)


# Categories
class NewCategoryForm(Form):
    name = StringField(_l('Name'), validators = [DataRequired()])
    public = BooleanField(_l('Public'))
    users = SelectMultipleField(_l('Allowed readers'), coerce = int,
                                widget = ListWidget(),
                                option_widget = CheckboxInput(),
                                choices = ClassChoices(User.query.order_by('login'), 'login'))

@app.route('/admin/categories')
@admin_required
def categories(form = None):
    if form is None:
        form = NewCategoryForm()
    return render_template('admin/categories.html', form = form,
                           categories = Category.query.all(),
                           delete_category = DeleteForm.for_class(Category))

@app.route('/admin/category/new', methods = ['POST'])
@admin_required
def new_category():
    form = NewCategoryForm()
    if form.validate():
        cat = Category()
        cat.name = form.name.data

        cat.public = form.public.data
        if not cat.public:
            cat.allowed_users.extend(User.query.filter(User.id.in_(form.users.data)))

        db.session.add(cat)
        try:
            db.session.commit()
            flash(_('Category added !'))
        except IntegrityError:
            flash(_("Category '%(category)s' already exists.", category = cat.name))

        return redirect(url_for('categories'))
    return categories(form)

@app.route('/admin/category/delete', methods = ['POST'])
@admin_required
def delete_category():
    if DeleteForm.validate_and_delete_for(Category):
        db.session.commit()
        flash(_('Category deleted !'))
    return redirect(url_for('categories'))

