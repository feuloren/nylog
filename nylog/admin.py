from flask import render_template, flash, redirect, url_for, abort, jsonify
from .app import app
from .models import db, User, Post, Comment, Category, IntegrityError
from sqlalchemy.orm import class_mapper
from .auth import admin_required
from flask_scrypt import generate_password_hash, generate_random_salt
from wtforms.validators import DataRequired
from wtforms import (StringField, HiddenField, PasswordField, BooleanField,
                     TextAreaField, DateField, SelectMultipleField,
                     IntegerField)
from wtforms.widgets import ListWidget, CheckboxInput, HiddenInput
from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug import secure_filename
from flask.ext.babel import gettext as _, lazy_gettext as _l
from datetime import date as dtdate
from uuid import uuid4 as random_uuid
from PIL import Image
import os.path

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
    posts = Post.query.order_by('covered_period')
    return render_template('admin/index.html', posts = posts)

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

@app.post('/admin/user/create')
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

@app.post('/admin/user/delete')
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

    def fill_post_object(self, post):
        post.title = self.title.data
        post.content = self.content.data
        post.covered_period = self.covered_period.data
        post.covers_week = self.week.data
        post.categories.extend(Category.query.filter(Category.name.in_(self.categories.data)))

        return post

@app.route('/admin/post/write')
@admin_required
def write_post():
    return render_template('admin/new_post.html', form = NewPostForm(prefix='post-'))

@app.post('/admin/post/new')
@admin_required
def new_post():
    form = NewPostForm(prefix='post-')
    if form.validate():
        post = Post()
        form.fill_post_object(post)
        post.slug = form.get_slug()
        
        db.session.add(post)
        db.session.commit()

        flash(_('Entry published !'))
        return redirect(url_for('write_post'))
    return render_template('admin/new_post.html', form = form)

class EditPostForm(NewPostForm):
    id = IntegerField(widget = HiddenInput(), validators = [DataRequired()])

@app.route('/admin/post/edit/<int:id>')
@admin_required
def edit_post(id, form = None):
    post = Post.query.get_or_404(id)
    if form is None:
        form = EditPostForm(prefix = 'post-')
        form.id.data = post.id
        form.title.data = post.title
        form.content.data = post.content
        form.covered_period.data = post.covered_period
        form.week.data = post.covers_week
        form.categories.data = (v[0] for v in post.categories.values('name'))
    return render_template('admin/update_post.html', form = form)

@app.post('/admin/post/update')
@admin_required
def update_post():
    form = EditPostForm(prefix = 'post-')
    if form.validate():
        post = Post.query.get_or_404(form.id.data)
        form.fill_post_object(post)
        # We don't change to slug

        db.session.commit()
        
        flash(_('Post "%(title)s" updated', title = post.title))
        return redirect(url_for('admin_home'))
    return render_template('admin/update_post.html', form = form)    

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

@app.post('/admin/category/new')
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

@app.post('/admin/category/delete')
@admin_required
def delete_category():
    if DeleteForm.validate_and_delete_for(Category):
        db.session.commit()
        flash(_('Category deleted !'))
    return redirect(url_for('categories'))


# Images
class ImageUploadForm(Form):
    image = FileField('image', validators = [FileRequired(),
                                             FileAllowed(('jpg', 'jpeg', 'png', 'gif'))])
    name = StringField('name')

@app.route('/admin/image/upload', methods = ['POST'])
@admin_required
def upload_image():
    form = ImageUploadForm()
    if form.validate():
        client_name, ext = os.path.splitext(form.image.data.filename)
        if not(ext):
            abort(400)

        dest_name = secure_filename(form.name.data)
        if not(dest_name):
            dest_name = str(random_uuid())
        dest_path = os.path.join('images', 'original', dest_name + ext)

        # TODO : handle name conflicts
        location = os.path.join(app.config['UPLOAD_FOLDER'], dest_path)
        form.image.data.save(location)
        # resize the image
        resized_path = resize_image(location, app.config['NYLOG_IMAGES_LARGE_WIDTH'])

        return jsonify({'original' : dest_path,
                        'resized' : resized_path})
    else:
        abort(400)

def resize_image(location, max_width):
    """Downscale an image if its width is greater than `max_width`
    Return the path of the new image (TODO move in outer function)
    """
    try:
        img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], location))
    except FileNotFoundError as e:
        return None

    width, height = img.size
    if width > max_width:
        ratio = height / width
        out = img.resize((max_width, int(max_width * ratio)))
        dest_path = os.path.join('images', 'large', os.path.basename(location))
        out.save(os.path.join(app.config['UPLOAD_FOLDER'], dest_path))
        return dest_path
    else:
        return None
