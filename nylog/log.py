from flask import render_template, abort, flash, redirect, url_for
from flask.ext.login import current_user
from .app import app
from .models import db, User, Post, Comment, Category, users_categories
from sqlalchemy.orm.exc import NoResultFound
from wtforms import TextAreaField, IntegerField
from wtforms.widgets import HiddenInput
from wtforms.validators import DataRequired
from flask.ext.babel import gettext as _, lazy_gettext as _l
from flask_wtf import Form

from .parsers import *

def posts_for_current_user():
    if not(current_user.is_anonymous()) and current_user.is_authenticated():
        if current_user.is_admin:
            # He can see everything
            return Post.query
        else:
            # They can see public posts and posts in their categories
            return Post.query.join(Post.categories).filter((Category.public == True) | Category.allowed_users.any(id = current_user.id))
    else:
        # They can only see public posts
        return Post.query.join(Post.categories).filter(Category.public == True)

@app.route('/')
def index():
    query = posts_for_current_user()
    posts = query.group_by(Post.id).order_by(Post.covered_period.desc()).limit(5)
    return render_template("home.html", posts = posts,
                           parse_post = summary_parser())


@app.route('/posts')
def old_posts():
    posts = Post.query.paginate(page, 5, error_out = False)
    return render_template("old.html", posts = posts)


@app.route('/post/<int:id>/<slug>')
def show_post(id, slug, comment_form = None):
    try:
        post = posts_for_current_user().filter(Post.id == id).one()
    except NoResultFound:
        abort(404)

    if comment_form is None:
        comment_form = CommentForm()
        comment_form.post.data = id

    return render_template("post.html", post = post, comment_form = comment_form,
                           display_comments = current_user.is_authenticated(),
                           parse_post = full_post_parser())

@app.post('/comment/add')
def save_comment():
    form = CommentForm()
    if form.validate():
        query = posts_for_current_user()
        try:
            post = query.filter(Post.id == form.post.data).one()
        except NoResultFound:
            abort(404)

        comment = Comment()
        comment.content = form.comment.data
        comment.post = post
        comment.author_id = current_user.id

        db.session.add(comment)
        db.session.commit()

        flash(_('Comment saved'))
        return redirect(url_for('show_post', id = post.id, slug = post.slug))
    else:
        if hasattr(form.post, 'data'):
            return show_post(form.post.data, '', form)
        else:
            abort(400)

class CommentForm(Form):
    post = IntegerField(widget = HiddenInput())
    comment = TextAreaField(_l('Leave a comment'), validators = [DataRequired()])
