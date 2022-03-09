from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user
from ..database import db, Project, Dataset, ProjectAccess
from ..dates import date_string
from ..types import AccessLevel
import uuid

projects = Blueprint("projects", __name__)

@projects.route("/project/<project_id>")
def view_project(project_id):
    project = Project.query.get(project_id)
    if project and current_user.can_edit(project):
        return render_template("view_project.html", project=project)
    else:
        flash("The selected project doesn't exist")
        return redirect(url_for("home.dashboard"))

@projects.route("/dataset/add/<project_id>", methods=["POST", "GET"])
def add_dataset(project_id):
    if request.method == "GET":
        return render_template("add_dataset.html")

    dataset_id = request.form.get("dataset_id")
    project = Project.query.get(project_id)
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        flash("The selected dataset doesn't exist")
        return render_template("add_dataset.html")

    if not project:
        flash("The selected project doesn't exist")
        return render_template("add_dataset.html")
    
    if not current_user.can_edit(project) or not current_user.can_edit(dataset):
        flash("Deprecated endpoint")
        return "Deprecated endpoint"

    project.datasets.append(dataset)
    db.session.commit()

    return redirect(url_for("projects.view_project", project_id=project_id))

@projects.route("/project/create", methods=["POST", "GET"])
def create_project():
    if request.method == "GET":
        return render_template("create_project.html")

    name = request.form.get("name")
    if not name:
        flash("Please supply a name")
        return render_template("create_project.html")

    if not current_user.is_authenticated:
        flash("Please log in")
        return render_template("create_project.html")

    user = current_user

    description = request.form.get("description")

    project = Project(
        id=uuid.uuid4().hex,
        name=name,
        description=description if description else f"Uploaded {date_string()}"
    )

    user.project_rights.append(
        ProjectAccess(
            user_id = user.id,
            project_id = project.id,
            access_level = AccessLevel.ADMIN
        )
    )


    db.session.add(project)
    db.session.commit()

    flash("Successfully created project")
    return redirect(url_for("home.dashboard"))


@projects.route("/project/delete", methods=["POST"])
def delete_project():
    project_id = request.form.get("project_id")
    confirm = request.form.get("confirm") == "true"
    project = Project.query.get(project_id)
    if not confirm:
        return render_template("delete_project.html", project=project)
    elif project:
        if not current_user.can_edit(project):
            flash("You can't delete this project")
            return redirect(url_for("home.dashboard"))
        db.session.delete(Project.query.get(project_id))
        db.session.commit()
    flash("The selected project doesn't exist")
    return redirect(url_for("home.dashboard"))
