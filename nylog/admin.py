from flask import render_template
from .app import app
from .models import db, User, Post, Comment
from .auth import admin_required

@app.route('/admin')
@admin_required
def admin_home():
    return "Not yet"

