from flask import Flask, request, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date

from flask_wtf import Form
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from wtforms import StringField, IntegerField, FloatField, SubmitField

from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


##CONFIGURE TABLES


class User(UserMixin, db.Model):
    __tablename__ = "blog_users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

    posts = relationship("BlogPost", back_populates="author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('blog_users.id'))
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

class MonthlyNeed(UserMixin, db.Model):
    __tablename__ = "monthly_needs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)


# Forms

class UserEditForm(Form):
    name = StringField('Nome')
    submit = SubmitField('Enviar')


class MonthlyNeedForm(Form):
    name = StringField('Nome')
    submit = SubmitField('Enviar')


with app.app_context():
    db.create_all()


def admin_only_post(function):
    def authentication(post_id):
        try:
            if current_user and current_user.id == 1:
                return function(post_id)
            return abort(403)
        except:
            return render_template("error_page.html")

    authentication.__name__ = function.__name__
    return authentication

def admin_only_need(function):
    def authentication_need(need_id):
        try:
            if current_user and current_user.id == 1:
                return function(need_id)
            return abort(403)
        except:
            return render_template("error_page.html")

    authentication_need.__name__ = function.__name__
    return authentication_need


def admin_only_page(function):
    def authentication_(page_id):

        try:
            if current_user and current_user.id == 1:
                return function(page_id)
            return abort(403)
        except:
            return render_template("error_page.html")

    authentication_.__name__ = function.__name__
    return authentication_

def admin_only(function):
    def authentication_empty():

        try:
            if current_user and current_user.id == 1:
                return function()
            return abort(403)
        except:
            return render_template("error_page.html")

    authentication_empty.__name__ = function.__name__
    return authentication_empty

def admin_only_user(function):
    def authentication_user(user_id):

        try:
            if current_user and current_user.id == 1:
                return function(user_id)
            return abort(403)
        except:
            return render_template("error_page.html")

    authentication_user.__name__ = function.__name__
    return authentication_user


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def get_all_posts():
    needs = MonthlyNeed.query.all()
    return render_template("index.html", date=date.today().strftime("%m/%Y"), needs= needs)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        if not User.query.filter_by(email=email).first():
            password = form.password.data
            hash_password = generate_password_hash(password)
            name = form.name.data
            new_user = User(email=email, password=hash_password, name=name)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
        else:
            error = "Você já se registrou. Faça o login."
            return render_template("register.html", form=form, error=error)
        return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=form)


@app.route('/login_casa_route', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":

        typed_email = request.form.get("email")
        typed_password = request.form.get("password")
        try:
            query_user = db.session.query(User).filter_by(email=typed_email).first()
            has_matched = check_password_hash(query_user.password, typed_password)
            if has_matched:
                login_user(query_user)
                flash('Logado com sucesso!')
                return redirect(url_for("get_all_posts"))
            else:
                error = 'Senha inválida.'
                return render_template("login.html", form=form, error=error)
        except Exception:
            error = 'Email inválido.'
            return render_template("login.html", form=form, error=error)

    return render_template("login.html", form=form)


@app.route('/logout_casa_route')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)

    return render_template("post.html", post=requested_post)


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

@app.route("/reports")
def reports():
    return redirect("https://drive.google.com/drive/folders/1BAF2wmnKE46DzqSb0qh_TYLaUiJkrjDf?usp=sharing")


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%d/%m/%Y")
        )

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)

# OK
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only_post
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)

# OK
@app.route("/delete/<int:post_id>")
@admin_only_post
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

# OK

@app.route("/admin")
@admin_only
def admin_page():
    return render_template("admin.html")

# OK

@app.route("/admin/users")
@admin_only
def user_list():
    users = User.query.order_by(User.name).all()
    return render_template("user_list.html", users=users)

# Creation


# Edit

# OK
@app.route("/edit-user/<int:user_id>", methods=["GET", "POST"])
@admin_only_user
def edit_user(user_id):
    user = User.query.get(user_id)
    edit_form = UserEditForm(
        name=user.name,
    )
    if edit_form.validate_on_submit():
        user.name = edit_form.name.data
        db.session.commit()
        return redirect(url_for("user_list"))

    return render_template("change_user.html", form=edit_form)

# OK
@app.route("/admin/needs")
@admin_only
def need_list():
    needs = MonthlyNeed.query.all()
    return render_template("need_list.html", needs=needs)

# OK
@app.route("/add-need", methods=["GET", "POST"])
@admin_only
def add_need():
    form = MonthlyNeedForm()
    if form.validate_on_submit():
        new_need = MonthlyNeed(
            name=form.name.data,
        )

        db.session.add(new_need)
        db.session.commit()
        return redirect(url_for("need_list"))
    return render_template("register_need.html", form=form)


# OK
@app.route("/add-need/<int:need_id>", methods=["GET", "POST"])
@admin_only_need
def edit_need(need_id):
    need = MonthlyNeed.query.get(need_id)
    edit_form = MonthlyNeedForm(
        name=need.name,

    )
    if edit_form.validate_on_submit():
        need.name = edit_form.name.data
        db.session.commit()
        return redirect(url_for("need_list", need_id=need.id))

    return render_template("register_need.html", form=edit_form, is_edit=True)


# OK
@app.route("/delete_need/<int:need_id>")
@admin_only_need
def delete_need(need_id):
    need_to_delete = MonthlyNeed.query.get(need_id)
    db.session.delete(need_to_delete)
    db.session.commit()
    return redirect(url_for('need_list'))

# OK
@app.route("/noticias")
def news():
    posts = BlogPost.query.order_by(BlogPost.date).all()[::-1]
    return render_template("news.html", all_posts=posts)


if __name__ == "__main__":
    app.run(debug=True)
