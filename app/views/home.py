from flask import Blueprint, url_for, redirect, render_template
from flask_login import current_user
from app.types import AccessLevel
from ..database import Project

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

    projects = []
    for access in current_user.project_rights:
        project = Project.query.get(access.project_id)
        print(access.access_level)
        if project and current_user.can_edit(project):
            projects.append(project)

    return render_template("dashboard.html", projects=projects)