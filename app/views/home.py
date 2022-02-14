from flask import Blueprint, url_for, redirect, render_template
from flask_login import current_user

home = Blueprint("home", __name__)

@home.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("home.dashboard"))

    return render_template("index.html")


@home.route("/dashboard")
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for("authentication.login"))

    projects = current_user.editable_projects()
    
    return render_template("dashboard.html", projects=projects)