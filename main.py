from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from datetime import date


import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)

Bootstrap(app)


@app.route('/')
def get_all_posts():
    return render_template("index.html", date=date.today().strftime("%m/%Y"))


@app.route("/sobre")
def about():
    return render_template("about.html")


@app.route("/projetos")
def projects():
    return render_template("projects.html")


@app.route("/missao")
def mission():
    return render_template("mission.html")


@app.route("/contato")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)
