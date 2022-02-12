from flask import Blueprint, render_template, url_for, redirect, request, flash, current_app, jsonify
from flask_login import current_user
from ..database import db, Project, Dataset, DatasetRow, DatasetRowValue
from ..types import Type
from ..dates import date_string
from werkzeug.utils import secure_filename
import tempfile
import os
import sqlite3
import uuid
import csv

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

    # TODO: Consider case when file is nefariously empty
    columns = next(reader)
    column_ids = []
    for column in columns:
        conn.execute(
            "INSERT INTO dataset_column (id, type, name, prompt, dataset_id) VALUES (?,?,?,?,?)",
            (dscid := uuid.uuid4().hex, Type.STRING.value, column, column, dataset.id)
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

@datasets.route("/dataset/<dataset_id>", methods=["GET"])
def view_dataset(dataset_id):
    # TODO: Check access
    dataset = Dataset.query.get(dataset_id)
    if dataset:
        return render_template("view_dataset.html", dataset=dataset, **Type.export())
    else:
        flash("The selected dataset doesn't exist")
        return redirect(url_for("datasets.show_datasets"))



@datasets.route("/dataset/import/<project_id>", methods=["POST", "GET"])
def import_dataset(project_id):
    if not current_user.is_authenticated:
        flash("Please log in to perform this action")
        return redirect(url_for("authentication.login"))

    # TODO: Check access rights
    if request.method == "GET":
        return render_template("import_dataset.html", project_id=project_id)

    # Check None (TODO)
    file = request.files.get("file")
    description = request.form.get("description")
    if not file:
        flash("Please submit a file")
        return render_template("import_dataset.html")

    dataset = read_dataset(file, current_app.config["DATABASE_LOCATION"], description=description)
    current_user.datasets.append(dataset)
    project = Project.query.get(project_id)
    if project:
        project.datasets.append(dataset)
        db.session.commit()
        return redirect(url_for('projects.view_project', project_id=project_id))
    flash("The selected project doesn't exit")
    return redirect(url_for("home.dashboard"))


@datasets.route("/dataset/update", methods=["POST"])
def update_dataset():
    # TODO: Access
    dataset_id = request.form.get('dataset_id')
    dataset = Dataset.query.get(dataset_id)
    
    if not dataset:
        flash("The selected dataset doesn't exist")
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
    return render_template("show_datasets.html")

@datasets.route("/dataset/<dataset_id>/nomore", methods=["GET"])
def no_more_data(dataset_id):
    flash("There is no more data for this dataset")
    return redirect(url_for("datasets.view_dataset", dataset_id=dataset_id))

@datasets.route("/dataset/nextrow", methods=["POST"])
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

@datasets.route("/dataset/code/<dataset_id>", methods=["GET", "POST"])
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


@datasets.route("/dataset/delete", methods=["POST"])
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

@datasets.route("/dataset/export", methods=["POST", "GET"])
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
