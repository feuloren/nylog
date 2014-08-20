from flask import render_template
from .app import app
from .models import db, User, Post, Comment, Category

@app.route('/')
def index():
    posts = Post.query.limit(5)#join(Post.categories).\
            #join(Category.users).\
            #filter()
    """SELECT * FROM post p JOIN posts_categories pc ON ...
    JOIN users_categories uc ON ...
    WHERE (uc.user IS NULL) OR (uc.user == $user)
    """
    return render_template("home.html", posts = posts)


@app.route('/posts')
def old_posts():
    posts = Post.query.paginate(page, 5, error_out = False)
    return render_template("old.html", posts = posts)


@app.route('/post/<int:id>/<slug>')
def show_post(id, slug):
    post = Post.query.get_or_404(id)
    return render_template("post.html", post = post)
