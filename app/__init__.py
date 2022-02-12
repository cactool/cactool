from flask import Flask, render_template, request, flash, url_for, redirect, send_file, jsonify, make_response
from passlib.hash import pbkdf2_sha256
from flask_login import LoginManager, login_user, current_user, logout_user
from app.database import db, User, Project, project_access, Dataset, DatasetColumn, DatasetRow, DatasetRowValue
from werkzeug.utils import secure_filename
from flask_migrate import Migrate

import app.types as types
import uuid
import csv
import datetime
import tempfile
import os
import os.path
import sqlite3
import json
import secrets

if not os.path.exists("config.json"):
    secret_key = secrets.token_urlsafe(64)
    with open("defaults/config.json") as file:
        config = json.load(file)
        config["secret-key"] = secret_key
    with open("config.json", "w") as file:
        json.dump(config, file, indent=2, sort_keys=True)
else:
    with open("config.json") as file:
        config = json.load(file)

DATABASE_LOCATION = "app/db.sqlite3"
DATABASE_URI = 'sqlite:///db.sqlite3'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = config["secret-key"]

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    try:
        db.create_all()
    except:
        pass



@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    return render_template("dashboard.html")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/project/<project_id>")
def view_project(project_id):
    # TODO: auth, existence check
    # flash(f"Viewing project with id {project_id}")
    return render_template("view_project.html", project=Project.query.get(project_id))


@app.route("/dataset/add/<project_id>", methods=["POST", "GET"])
def add_dataset(project_id):
    # TODO: Move project_id out of URL
    # TODO: Access control
    if request.method == "GET":
        return render_template("add_dataset.html")

    dataset_id = request.form.get("dataset_id")
    project = Project.query.get(project_id)
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        flash("Selected dataset doesn't exist")
        return render_template("add_dataset.html")

    if not project:
        flash("Selected project doesn't exist")
        return render_template("add_dataset.html")

    project.datasets.append(dataset)
    db.session.commit()

    return redirect(url_for("view_project", project_id=project_id))


def date_string():
    return datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")


@app.route("/datasets", methods=["GET"])
def show_datasets():
    return render_template("show_datasets.html")


def read_dataset(file, description=None):
    conn = sqlite3.connect(DATABASE_LOCATION)
    conn.execute("pragma journal_mode=wal")
    reader = csv.reader(file.read().decode().splitlines())

    dataset = Dataset(
        id=uuid.uuid4().hex,
        name=secure_filename(file.filename),
        description=f"Uploaded {date_string()}" if not description else description
    )

    db.session.add(dataset)
    db.session.commit()

    # Using sqlite3 for performance

    # TODO: Consider case when file is nefariously empty
    columns = next(reader)
    column_ids = []
    for column in columns:
        conn.execute(
            "INSERT INTO dataset_column (id, type, name, dataset_id) VALUES (?,?,?,?)",
            (dscid := uuid.uuid4().hex, types.Type.STRING.value, column, dataset.id)
        )
        
        column_ids.append(dscid)

    for row_number, row in enumerate(reader):
        values = row
        
        conn.execute(
            "INSERT INTO dataset_row (dataset_id, row_number, coded) VALUES (?, ?, ?)",
            (dataset.id, row_number, False)
        )

        for column_id, value in zip(column_ids, values):
            conn.execute(
                "INSERT INTO dataset_row_value (dataset_id, dataset_row_number, column_id, value) VALUES (?, ?, ?, ?)",
                (dataset.id, row_number, column_id, value)
            )

    conn.commit()

    db.session.add(dataset)
    db.session.commit()

    return dataset


@app.route("/dataset/<dataset_id>", methods=["GET"])
def view_dataset(dataset_id):
    # TODO: Check Existence, Check access
    dataset = Dataset.query.get(dataset_id)
    return render_template("view_dataset.html", dataset=dataset, **types.Type.export())

@app.route("/dataset/<dataset_id>/nomore", methods=["GET"])
def no_more_data(dataset_id):
    flash("There is no more data for this dataset")
    return url_for(view_dataset, dataset_id=dataset_id)


@app.route("/dataset/nextrow", methods=["POST"])
def next_row():
    # TODO: Existence, access
    dataset_id = request.json["dataset_id"]
    dataset = Dataset.query.get(dataset_id)
    rows = filter(
        lambda row: not row.coded,
        dataset.rows
    )

    try:
        row = next(rows).serialise()
    except StopIteration:
        row = {"is_empty": True}

    return jsonify(row)


@app.route("/dataset/update", methods=["POST"])
def update_dataset():
    # TODO: Access, existence
    dataset_id = request.form.get('dataset_id')
    dataset = Dataset.query.get(dataset_id)

    for column in dataset.columns:
        given_datatype = request.form.get(column.name)
        if given_datatype:
            column.type = given_datatype
    db.session.commit()

    return redirect(url_for("view_dataset", dataset_id=dataset_id))


@app.route("/dataset/code/<dataset_id>", methods=["GET", "POST"])
def code_dataset(dataset_id):
    # TODO: Check access, existence
    dataset = Dataset.query.get(dataset_id)
    if request.method == "GET":
        return render_template("code_dataset.html", dataset=dataset)
    data = request.json
    row_number = data["row_number"]
    row = DatasetRow.query.get((dataset_id, row_number))
    if data.get("skip"):
        row.skip = True
    elif data.get("post_unavailable"):
        row.post_unavailable = True
    else:
        for (column_id, value) in data["values"].items():
            row_value = DatasetRowValue.query.get(
                (dataset_id, row_number, column_id))
            row_value.value = value
    row.coded = True
    row.coder = current_user.id
    db.session.commit()
    return next_row()


@app.route("/dataset/delete", methods=["POST"])
def delete_dataset():
    dataset_id = request.form.get("dataset_id") # TODO: Check if undefined
    confirm = request.form.get("confirm") == "true"
    # TODO: Check access, query
    dataset = Dataset.query.get(dataset_id)
    if not confirm:
        return render_template("delete_dataset.html", dataset=dataset)
    else:

        dataset = Dataset.query.get(dataset_id)
        db.session.delete(dataset)
        db.session.commit()
        
        return redirect(url_for("show_datasets"))


@app.route("/project/delete", methods=["POST"])
def delete_project():
    project_id = request.form.get("project_id")
    confirm = request.form.get("confirm") == "true"
    # TODO: Check access, query
    project = Project.query.get(project_id)
    if not confirm:
        return render_template("delete_project.html", project=project)
    else:
        db.session.delete(Project.query.get(project_id))
        db.session.commit()

        return redirect(url_for("dashboard"))


@app.route("/dataset/import/<project_id>", methods=["POST", "GET"])
def import_dataset(project_id):
    if not current_user.is_authenticated:
        flash("Please log in to perform this action")
        return redirect(url_for("login"))

    # TODO: Check access rights, and existence
    if request.method == "GET":
        return render_template("import_dataset.html", project_id=project_id)

    # Check None (TODO)
    file = request.files.get("file")
    description = request.form.get("description")
    if not file:
        flash("Please submit a file")  # TODO: Error
        return render_template("import_dataset.html")

    dataset = read_dataset(file, description=description)
    current_user.datasets.append(dataset)
    # TODO: Check existence
    project = Project.query.get(project_id)
    project.datasets.append(dataset)
    db.session.commit()
    return redirect(url_for('view_project', project_id=project_id))


@app.route("/dataset/export", methods=["POST", "GET"])
def export_dataset():
    if not current_user.is_authenticated:
        flash("Please log in to perform this action")
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("export_dataset.html")

    dataset_id = request.form.get("dataset_id")
    if not dataset_id:
        flash("Please select a dataset")  # TODO: Error
        return render_template("export_dataset.html")

    # Check access (TODO)
    # Check existence (TODO)

    fd, path = tempfile.mkstemp()

    dataset = Dataset.query.get(dataset_id)

    with open(path, "w") as file:
        writer = csv.DictWriter(  # TODO: Unique constraint on fieldnames
            file,  # Denial of service? (TODO)
            fieldnames=list(map(
                lambda column: column.name,
                dataset.columns
            )) + ["coder", "coded"]
        )

        writer.writeheader()

        for row in dataset.rows:
            writer.writerow(
                {
                    entry.column.name: entry.value for entry in row.values
                }
                | {
                    "coder": row.coder.initials() if row.coder is not None else "",
                    "coded": row.coded,
                    "skip": row.skip
                }
            )
        file.close()

    response = send_file(
        path,
        as_attachment=True,
        download_name=f"{dataset.name}",
        # last_modified = # TODO possibly work out last modified time
    )

    os.unlink(path)
    os.close(fd)

    return response


@app.route("/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/project/create", methods=["POST", "GET"])
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

    user.projects.append(project)

    db.session.add(project)
    db.session.commit()

    flash("Successfully created project")
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["POST", "GET"])
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

        return redirect(url_for("dashboard"))


def password_strength(password):
    # Very basic password strength requirements
    if len(password) >= 8 \
            and any(map(str.isalpha, password))\
            and any(map(str.isnumeric, password)):
        return True
    return False


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        flash("Passwords must have 8 or more characters and must contain a number and a letter")
        return render_template("signup.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        firstname = request.form.get("firstname")
        surname = request.form.get("surname")

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("A user with this username already exists")

        elif username and password and firstname and surname:
            if not password_strength(password):
                flash("Your password isn't strong enough")  # TODO: Explain
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

            flash("Successfilly created an account")

        else:
            flash("Some fields were left blank")

        return redirect(url_for("login"))


if __name__ == "__main__":
    app = create_app()
    app.run()
