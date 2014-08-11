from flask import Flask, render_template

app = Flask('nylog')

@app.errorhandler(404)
def handler_page_not_found(e):
    return render_template("404.html"), 404
