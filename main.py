from flask import Flask, request, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date

from flask_wtf import Form, validators
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
    comments = relationship("Comment", back_populates="author")


class Child(UserMixin, db.Model):
    __tablename__ = "institution_children"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Worker(UserMixin, db.Model):
    __tablename__ = "institution_workers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Donation(UserMixin, db.Model):
    __tablename__ = "donations"
    id = db.Column(db.Integer, primary_key=True)
    donator_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('blog_users.id'))
    author = relationship("User", back_populates="posts")

    comments = relationship("Comment", back_populates="post")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('blog_users.id'))
    author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    post = relationship("BlogPost", back_populates="comments")

    text = db.Column(db.Text, nullable=False)

# Forms


class CreateChildForm(Form):
    name = StringField('Nome')


class CreateWorkerForm(Form):
    name = StringField('Nome')


class CreateDonationForm(Form):
    name = StringField('Nome')
    amount = StringField('Quantia')
    submit = SubmitField('Enviar')


db.create_all()


def admin_only(function):
    def authentication(post_id):
        if current_user and current_user.id == 1:
            return function(post_id)
        return abort(403)

    authentication.__name__ = function.__name__
    return authentication


def admin_only_page(function):
    def authentication2():
        if current_user and current_user.id == 1:
            return function()
        return abort(403)

    authentication2.__name__ = function.__name__
    return authentication2


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


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


@app.route('/login', methods=["GET", "POST"])
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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    comments = db.session.query(Comment).filter_by(post_id=post_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Você precisa fazer login ou se registrar para comentar.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=form.comment_text.data,
            author_id=current_user.id,
            post_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", post=requested_post, form=form, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )

        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
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
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/admin")
@admin_only_page
def admin_page():
    return render_template("admin.html")


@app.route("/admin/users")
@admin_only_page
def user_list():
    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/admin/children")
@admin_only_page
def child_list():
    children = Child.query.all()
    return render_template("child_list.html", children=children)


@app.route("/admin/workers")
@admin_only_page
def workers_list():
    workers = Worker.query.all()
    return render_template("worker_list.html", workers=workers)


@app.route("/admin/donations")
@admin_only_page
def donation_list():
    donations = Donation.query.all()
    return render_template("donation_list.html", donations=donations)

# Creation

@app.route("/new-child", methods=["GET", "POST"])
@admin_only_page
def add_new_child():
    form = CreateChildForm()
    if form.validate_on_submit():
        new_child = Child(
            name=form.name.data,
        )

        db.session.add(new_child)
        db.session.commit()
        return redirect(url_for("child_list"))
    return render_template("register_child.html", form=form)


@app.route("/new-worker", methods=["GET", "POST"])
@admin_only_page
def add_new_worker():
    form = CreateWorkerForm()
    if form.validate_on_submit():
        new_worker = Worker(
            name=form.name.data,
        )

        db.session.add(new_worker)
        db.session.commit()
        return redirect(url_for("workers_list"))
    return render_template("register_worker.html", form=form)

@app.route("/new-donation", methods=["GET", "POST"])
@admin_only_page
def add_new_donation():
    form = CreateDonationForm()
    if form.validate_on_submit():

        new_donation = Donation(
            donator_name=form.name.data,
            amount = float(form.amount.data)
        )


        db.session.add(new_donation)
        db.session.commit()
        return redirect(url_for("donation_list"))
    return render_template("register_donation.html", form=form)

# Deletion

@app.route("/delete_child/<int:child_id>")
def delete_child(child_id):
    child_to_delete = Child.query.get(child_id)
    db.session.delete(child_to_delete)
    db.session.commit()
    return redirect(url_for('child_list'))

@app.route("/delete_worker/<int:worker_id>")
def delete_worker(worker_id):
    worker_to_delete = Worker.query.get(worker_id)
    db.session.delete(worker_to_delete)
    db.session.commit()
    return redirect(url_for('workers_list'))

@app.route("/delete_donation/<int:donation_id>")
def delete_donation(donation_id):
    donation_to_delete = Donation.query.get(donation_id)
    db.session.delete(donation_to_delete)
    db.session.commit()
    return redirect(url_for('donation_list'))



if __name__ == "__main__":
    app.run(debug=True)
