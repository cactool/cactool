from flask import Blueprint, render_template, url_for, redirect, request, flash, current_app, jsonify, send_file
from flask_login import current_user
from ..database import db, Project, Dataset, DatasetRow, DatasetRowValue, DatasetAccess, AccessLevel
from ..types import Type
from ..dates import date_string
from werkzeug.utils import secure_filename
import tempfile
import os
import sqlite3
import uuid
import csv
import requests
from sqlalchemy import select

datasets = Blueprint("datasets", __name__)

def read_dataset(file, database_location, description=None):
    conn = sqlite3.connect(database_location)
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

    try:
        columns = next(reader)
    except StopIteration:
        flash("The uploaded file was malformed")
        redirect(url_for("datasets.show_datasets"))

    column_ids = []
    for column in columns:
        conn.execute(
            "INSERT INTO dataset_column (id, type, name, prompt, dataset_id) VALUES (?,?,?,?,?)",
            (dscid := uuid.uuid4().hex, Type.STRING.value, column, column, dataset.id)
        )
        
        column_ids.append(dscid)

    chunk_size = current_app.config["max_rows_in_memory"]
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
        
        if chunk_size != -1 and row_number % chunk_size:
            conn.commit()

    conn.commit()

    db.session.add(dataset)
    db.session.commit()

    return dataset

@datasets.route("/dataset/invite/<dataset_id>/<invite_code>", methods=["GET"])
def dataset_invite(dataset_id, invite_code):
    if not current_user:
        flash("You need to be logged in to complete this action")
        return redirect(url_for("authentication.login"))

    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        return "The selected dataset doesn't exist"
    if dataset.confirm(bytes.fromhex(invite_code), current_app.encryption_key):
        if not current_user.can_code(dataset):
            current_user.dataset_rights.append(
                DatasetAccess(
                    dataset,
                    AccessLevel.CODE
                )
            )
            return redirect(url_for("datasets.view_dataset", dataset_id=dataset.id))
        else:
            flash("You already have access to this dataset")
            return redirect(url_for("datasets.view_dataset", dataset_id=dataset.id))
    else:
        return f"The incorrect code was supplied"

@datasets.route("/dataset/<dataset_id>", methods=["GET"])
def view_dataset(dataset_id):
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        flash("The selected dataset doesn't exist")
        return redirect(url_for("datasets.show_datasets"))

    if not current_user.can_edit(dataset):
        flash("You don't have access to that dataset")
        redirect(url_for("datasets.show_datasets"))

    return render_template(
        "view_dataset.html",
        dataset=dataset,
        **Type.export(),
        invite_link=dataset.generate_invite_link(
            request.host_url,
            current_app.encryption_key
        )
    )
    


@datasets.route("/dataset/import/<project_id>", methods=["POST", "GET"])
def import_dataset(project_id):
    if not current_user.is_authenticated:
        flash("Please log in to perform this action")
        return redirect(url_for("authentication.login"))

    project = Project.query.get(project_id)

    if not project:
        flash("The selected project doesn't exit")
        return redirect(url_for("home.dashboard"))

    if not current_user.can_edit(project):
        flash(message)
        return redirect(url_for("home.dashboard"))

    if request.method == "GET":
        return render_template("import_dataset.html", project_id=project_id)

    file = request.files.get("file")
    description = request.form.get("description")
    if not file:
        flash("Please submit a file")
        return render_template("import_dataset.html")

    dataset = read_dataset(file, current_app.config["DATABASE_LOCATION"], description=description)
    
    current_user.dataset_rights.append(
        DatasetAccess(
            user_id=current_user.id,
            dataset_id=dataset.id,
            access_level=AccessLevel.ADMIN
        )
    )
    
    project.datasets.append(dataset)
    db.session.commit()
    return redirect(url_for('projects.view_project', project_id=project_id))


@datasets.route("/dataset/update", methods=["POST"])
def update_dataset():
    dataset_id = request.form.get('dataset_id')
    dataset = Dataset.query.get(dataset_id)
    
    if not dataset:
        flash("The selected dataset doesn't exist")
        redirect(url_for("datasets.show_datasets"))
    
    if not current_user.can_edit(dataset):
        flash("You do not have access to this dataset")
        redirect(url_for("datasets.show_datasets"))

    for column in dataset.columns:
        datatype = request.form.get(column.name + "-type")
        prompt = request.form.get(column.name + "-prompt")
        if datatype:
            column.type = datatype
        if prompt or column.type == Type.HIDDEN:
            column.prompt = prompt
    db.session.commit()

    return redirect(url_for("datasets.view_dataset", dataset_id=dataset_id))


@datasets.route("/datasets", methods=["GET"])
def show_datasets():
    return render_template("show_datasets.html", datasets=current_user.viewable_datasets())

@datasets.route("/dataset/<dataset_id>/nomore", methods=["GET"])
def no_more_data(dataset_id):
    flash("There is no more data for this dataset")
    return redirect(url_for("datasets.show_datasets", dataset_id=dataset_id))

@datasets.route("/dataset/nextrow", methods=["POST"])
def next_row():
    dataset_id = request.json["dataset_id"]
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        flash("The selected dataset doesn't exist")
        return redirect(url_for("datasets.view_datasets"))
    if not current_user.can_code(dataset):
        flash("You don't have access to this dataset")
        return redirect(url_for("datasets.view_datasets"))
    
    row = DatasetRow.query.filter_by(dataset_id=dataset_id, coded=False).first()

    if row:
        row = row.serialise()
    else:
        row = {"is_empty": True}

    return jsonify(row)

@datasets.route("/dataset/code/<dataset_id>", methods=["GET", "POST"])
def code_dataset(dataset_id):
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        flash("The selected dataset doesn't exist")
        return redirect(url_for("datasets.view_datasets"))
    if not current_user.can_code(dataset):
        flash("You don't have access to this dataset")
        redirect(url_for("datasets.show_datasets"))
    if request.method == "GET":
        return render_template("code_dataset.html", dataset=dataset)
    data = request.json
    row_number = data["row_number"]
    row = DatasetRow.query.get((dataset_id, row_number))
    if data.get("skip"):
        row.skip = True
        row.post_unavailable = False
    elif data.get("post_unavailable"):
        row.post_unavailable = True
        row.skip = False
    else:
        row.skip = False
        row.post_unavailable = False
        for (column_id, value) in data["values"].items():
            row_value = DatasetRowValue.query.get(
                (dataset_id, row_number, column_id))
            row_value.value = value
    row.coded = True
    row.coder = current_user
    db.session.commit()
    return next_row()

@datasets.route("/dataset/code/tiktok/<dataset_id>/<row_number>/<column_id>", methods=["GET"])
def render_tiktok(dataset_id, row_number, column_id):
    dataset = Dataset.query.get(dataset_id)
    if not dataset or not current_user.can_code(dataset):
        flash("You don't have access to that dataset")
        return redirect(url_for("show_datasets"))
    row_value = DatasetRowValue.query.get((dataset_id, row_number, column_id))

    url = row_value.value 
    domain = requests.utils.urlparse(url)

    response = requests.get(f"https://www.tiktok.com/oembed?url={requests.utils.quote(url)}")
    
    return jsonify(response.json())


@datasets.route("/dataset/delete", methods=["POST"])
def delete_dataset():
    dataset_id = request.form.get("dataset_id")
    confirm = request.form.get("confirm") == "true" # Only if the confirm string is exactly "true"
    dataset = Dataset.query.get(dataset_id)
    
    if not confirm:
        return render_template("delete_dataset.html", dataset=dataset)
    else:
        if not dataset:
            return redirect(url_for("datasets.show_dataset"))
        if not current_user.can_edit(dataset):
            flash("You don't have access to this dataset")
            return redirect(url_for("datasets.show_datasets"))
        dataset = Dataset.query.get(dataset_id)
        db.session.delete(dataset)
        db.session.commit()
        
        return redirect(url_for("show_datasets"))

def dict_union(dict1, dict2):
    return {**dict1, **dict2}

@datasets.route("/dataset/export", methods=["POST", "GET"])
def export_dataset():
    if not current_user.is_authenticated:
        flash("Please log in to perform this action")
        return redirect(url_for("authentication.login"))

    if request.method == "GET":
        return render_template("export_dataset.html")

    dataset_id = request.form.get("dataset_id")
    if not dataset_id:
        flash("Please select a dataset")
        return render_template("export_dataset.html")

    fd, path = tempfile.mkstemp()

    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        flash("The selected dataset doesn't exist")
        return redirect(url_for("view_datasets"))
    
    if not current_user.can_export(dataset):
        flash("You can't export this dataset")
        return redirect(url_for("datasets.show_dataset"))

    with open(path, "w") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(map(
                lambda column: column.name,
                dataset.columns
            )) + ["coded", "coder", "post_unavailable", "skipped"]
        )

        writer.writeheader()

        for row in dataset.rows:
            writer.writerow(
                dict_union(
                    {
                        entry.column.name: entry.value for entry in row.values
                    },
                    {
                        "coder": row.coder.initials() if row.coder is not None else "",
                        "coded": row.coded,
                        "skipped": row.skip, 
                        "post_unavailable": row.post_unavailable
                    }
                )
            )
        file.close()

    response = send_file(
        path,
        as_attachment=True,
        download_name=f"{dataset.name}",
    )

    os.unlink(path)
    os.close(fd)

    return response
