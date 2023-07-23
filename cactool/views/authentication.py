import email.utils
import secrets
import smtplib
import ssl
import time

import pyotp
import qrcode
import qrcode.image.svg
from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import login_user, logout_user
from passlib.hash import pbkdf2_sha256

from ..database import User, UserEmailVerification, db

authentication = Blueprint("authentication", __name__)


def send_email(email, message):
    details = current_app.config["mail-server"]
    context = ssl.create_default_context()
    host = details["host"]
    port = details["port"]
    username = details["port"]
    password = details["port"]
    sender_email = details["email"]

    if not (host and port and username and password and sender_email):
        raise Exception("Unable to send e-mail: server details not present")

    server = smtplib.SMTP(details["host"], details["port"])
    server.starttls()
    server.login(username, password)
    server.sendmail(sender_email, email, message)


def password_strength(password):
    if (
        len(password) >= 8
        and any(map(str.isalpha, password))
        and any(map(str.isnumeric, password))
    ):
        return True
    return False


@authentication.route("/verify-email/<verification_code>")
def verify_email(verification_code):
    email_verification = UserEmailVerification.query.get(verification_code)
    email_verification.user.unverified = False
    email_verification.delete()
    db.session.commit()
    flash("Email verified")
    return redirect(url_for(login))


@authentication.route("/setup-2fa", methods=["POST", "GET"])
def setup_2fa():
    if not session["2fa-username"]:
        return redirect(url_for("authentication.login"))

    if request.method == "POST":
        username = session["2fa-username"]
        user = User.query.filter_by(username=username).first()
        if not user:
            session.pop("2fa-username", None)
            session.pop("2fa-url", None)
            return redirect(url_for("authentication.login"))

        otp = request.form.get("otp")
        totp = pyotp.TOTP(session["2fa-secret"])

        if totp.verify(otp):
            user.otp_secret = session["2fa-secret"]
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for("home.dashboard"))

        flash("Incorrect 2FA code entered")

    qrcode_image = qrcode.make(
        session["2fa-url"], image_factory=qrcode.image.svg.SvgImage
    ).to_string()
    return render_template("setup_2fa.html", qrcode=qrcode_image.decode())


@authentication.route("/verify-2fa", methods=["POST", "GET"])
def verify_2fa():
    if not session["2fa-username"]:
        return redirect(url_for("authentication.login"))

    user = User.query.filter_by(username=session["2fa-username"]).first()
    if not user:
        return redirect(url_for("authentication.login"))
    if request.method == "POST":
        otp = request.form.get("otp")
        totp = pyotp.TOTP(session["2fa-secret"])
        if totp.verify(otp):
            login_user(user, remember=True)
            return redirect(url_for("home.dashboard"))
        flash("Incorrect 2FA code")
    return render_template("verify_2fa.html")


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
            if current_app.config["require-2fa"] and not user.has_2fa:
                otp_secret = User.random_otp_secret()
                session["2fa-username"] = username
                session["2fa-secret"] = otp_secret
                session["2fa-url"] = User.otp_secret_to_url(
                    otp_secret, username=username
                )
                return redirect(url_for("authentication.setup_2fa"))
            if user.has_2fa:
                session["2fa-username"] = username
                session["2fa-secret"] = user.otp_secret
                return redirect(url_for("authentication.verify_2fa"))
            else:
                if user.unverified:
                    flash("Your e-mail has not yet been verified")
                    return redirect(url_for(login))
                login_user(user, remember=True)
                flash("Logged in successfully")
        else:
            flash("You entered the wrong password for this account")
            return redirect(url_for("login"))

        return redirect(url_for("home.dashboard"))


@authentication.route("/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("home.index"))


@authentication.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    if request.method == "POST":
        code = current_app.config["signup-code"]
        if code:
            if request.form.get("signup-code") != code:
                flash("The signup code entered was not correct")
                return render_template("signup.html")

        username = request.form.get("username")
        password = request.form.get("password")
        firstname = request.form.get("firstname")
        surname = request.form.get("surname")
        email = request.form.get("email")

        require_email = current_app.config["require-email"]
        email_domains = current_app.config["email-domains"]
        should_verify_emails = current_app.config["verify-emails"]

        if require_email:
            if email is None or not email:
                flash("You must provide an email")
                return render_template("signup.html")
            _name, address = email.utils.parseaddr(email)
            if not address:
                flash("The email provided was not valid")
                return render_template("signup.html")

            authorised = any(email.endswith(f"@{domain}") for domain in email_domains)
            if email_domains and not authorised:
                flash(
                    "The provided email is not authorised to create an account on this site"
                )
                return render_template("signup.html")

        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash("A user with this username already exists")
            return render_template("signup.html")

        if email and existing_email:
            flash("A user with the provided email already exists")
            return render_template("signup.html")

        if not (username and password and firstname and surname):
            flash("Some fields were left blank")
            return render_template("signup.html")

        if not password_strength(password):
            flash("Your password isn't strong enough")
            return render_template("signup.html")

        hashed_password = pbkdf2_sha256.hash(password)
        user = User(
            username=username,
            password=hashed_password,
            firstname=firstname,
            surname=surname,
            email=email,
            unverified=should_verify_emails,
            id=secrets.token_hex(8),
        )

        if email and should_verify_emails:
            verification_code = secrets.token_hex(8)
            send_email(
                email,
                f"Welcome to cactool! Your verification code is {request.host_url}verify-email/{verification_code}",
            )
            user.email_verification = [
                UserEmailVerification(
                    verification_code=verification_code,
                    user_id=user.id,
                    # 14 days
                    timestamp=round(time.time() + 60 * 60 * 24 * 14),
                )
            ]

        db.session.add(user)
        db.session.commit()

        flash("Successfully created an account")

        return redirect(url_for("authentication.login"))
