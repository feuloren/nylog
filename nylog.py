from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/post/<int:id>/<slug>')
def show_post(id,  slug):
    return render_template("post.html", title = slug, id = id)

if __name__ == '__main__':
    app.run(debug = True)
