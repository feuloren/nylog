from flask import render_template
from .app import app
from .models import db, User

def set_logged_user():
    pass

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    pass

@app.route('/logout')
def logout():
    pass

