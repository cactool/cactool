from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from ..database import db, User
from flask_login import login_user, logout_user
from passlib.hash import pbkdf2_sha256
import secrets

authentication = Blueprint("authentication", __name__)

def password_strength(password):
    if len(password) >= 8 \
            and any(map(str.isalpha, password))\
            and any(map(str.isnumeric, password)):
        return True
    return False

@authentication.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if not user:
            flash("No user with that username exists")
        elif pbkdf2_sha256.verify(password, user.password):
            login_user(
                user,
                remember=True
            )
            flash("Logged in successfully")
        else:
            flash("You enterred the wrong password for this account")

        return redirect(url_for("home.dashboard"))


@authentication.route("/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("home.index"))

@authentication.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        flash("Passwords must have 8 or more characters and must contain a number and a letter")
        return render_template("signup.html", use_code=current_app.config["signup-code"] is not None)
    if request.method == "POST":
        if (code := current_app.config["signup-code"]) is not None:
            if request.form.get("signup-code") != code:
                flash("The signup code entered was not correct")
                return render_template("signup.html") 
        username = request.form.get("username")
        password = request.form.get("password")
        firstname = request.form.get("firstname")
        surname = request.form.get("surname")

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("A user with this username already exists")

        elif username and password and firstname and surname:
            if not password_strength(password):
                flash("Your password isn't strong enough")
                return render_template("signup.html")
            hashed_password = pbkdf2_sha256.hash(password)
            user = User(
                username=username,
                password=hashed_password,
                firstname=firstname,
                surname=surname,
                id=secrets.token_hex(8)
            )
            db.session.add(user)
            db.session.commit()

            flash("Successfully created an account")

        else:
            flash("Some fields were left blank")

        return redirect(url_for("authentication.login"))