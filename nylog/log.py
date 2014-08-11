from flask import render_template
from .app import app
from .models import db, User, Post, Comment

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/post/<int:id>/<slug>')
def show_post(id,  slug):
    return render_template("post.html", title = slug, id = id)
