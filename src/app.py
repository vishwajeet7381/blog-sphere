import os

from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["UPLOAD_FOLDER"] = "uploads"  # Folder to store uploaded images
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    posts = db.relationship("Post", backref="user", lazy=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    background_image = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


@app.route("/")
def home():
    posts = Post.query.all()
    return render_template("home.html", posts=posts)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["logged_in"] = True
            return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("logged_in", None)
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password, method="sha256")

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        # Handle file upload
        if "background_image" in request.files:
            file = request.files["background_image"]

            if file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
            else:
                filename = None
        else:
            filename = None

        new_post = Post(
            title=title,
            content=content,
            background_image=filename,
            user_id=session["user_id"],
        )
        db.session.add(new_post)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("create_post.html")


@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    post = Post.query.get(post_id)

    if post.user_id != session["user_id"]:
        return redirect(url_for("home"))

    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        post.background_image = request.form["background_image"]
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit_post.html", post=post)


@app.route("/delete_post/<int:post_id>")
def delete_post(post_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    post = Post.query.get(post_id)

    if post.user_id != session["user_id"]:
        return redirect(url_for("home"))

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    posts = Post.query.filter_by(user_id=user.id).all()

    return render_template("profile.html", user=user, posts=posts)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
