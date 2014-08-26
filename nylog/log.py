from flask import render_template
from flask.ext.login import current_user
from .app import app
from .models import db, User, Post, Comment, Category, users_categories
from sqlalchemy.sql.expression import literal

@app.route('/')
def index():
    if not(current_user.is_anonymous()) and current_user.is_authenticated():
        if current_user.is_admin:
            # He can see everything
            query = Post.query
        else:
            # They can see public posts and posts in their categories
            query = Post.query.join(Post.categories).filter((Category.public == True) | Category.allowed_users.any(id = current_user.id))
    else:
        # They can only see public posts
        query = Post.query.join(Post.categories).filter(Category.public == True)

    posts = query.group_by(Post.id).order_by(Post.covered_period).limit(5)
    return render_template("home.html", posts = posts)


@app.route('/posts')
def old_posts():
    posts = Post.query.paginate(page, 5, error_out = False)
    return render_template("old.html", posts = posts)


@app.route('/post/<int:id>/<slug>')
def show_post(id, slug):
    post = Post.query.get_or_404(id)
    return render_template("post.html", post = post)
