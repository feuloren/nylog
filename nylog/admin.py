from flask import render_template
from .app import app
from .models import db, User, Post, Comment

@app.route('/admin/')
def admin_home():
    return "Not yet"

