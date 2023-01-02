import csv
import itertools
import os
import sqlite3
import tempfile
import uuid

import requests
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user
from sqlalchemy import select
from werkzeug.utils import secure_filename

from ..database import (
    AccessLevel,
    Dataset,
    DatasetAccess,
    DatasetRow,
    DatasetRowValue,
    Project,
    db,
)
from ..dates import date_string
from ..types import Type

datasets = Blueprint("datasets", __name__)


def process_row(row_data):
    (dataset_id, column_ids), (row_number, values) = row_data
    entries = []
    for column_id, value in zip(column_ids, values):
        entries.append((dataset_id, row_number, column_id, value))

    return entries


def read_dataset(file, database_location, description=None):
    conn = sqlite3.connect(database_location)
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma synchronous = normal")
    conn.execute("pragma cache_size = -102400")

    reader = csv.reader(file.read().decode().splitlines())

    dataset = Dataset(
        id=uuid.uuid4().hex,
        name=secure_filename(file.filename),
        description=f"Uploaded {date_string()}" if not description else description,
    )

    db.session.add(dataset)
    db.session.commit()

    # Using sqlite3 for performance

    try:
        columns = next(reader)
    except StopIteration:
        return False

    column_ids = []
    for index, column in enumerate(columns):
        conn.execute(
            """
            INSERT INTO dataset_column (
                id, type, name,
                prompt, dataset_id, `order`
            )
            VALUES (
                ?, ?, ?,
                ?, ?, ?
            )
            """,
            (
                column_id := uuid.uuid4().hex,
                Type.STRING.value,
                column,
                column,
                dataset.id,
                index + 1,
            ),
        )

        column_ids.append(column_id)

    row_value_entries = tuple(
        itertools.chain.from_iterable(
            map(
                process_row,
                zip(itertools.repeat((dataset.id, column_ids)), enumerate(reader)),
            )
        )
    )

    total_rows = len(row_value_entries) // len(column_ids)

    conn.executemany(
        """
        INSERT INTO dataset_row (
            dataset_id, row_number,
            coded, skip, post_unavailable
        )
        VALUES (
            ?, ?,
            ?, ?, ?
        )
        """,
        [
            (dataset.id, row_number, False, False, False)
            for row_number in range(total_rows)
        ],
    )

    conn.executemany(
        "INSERT INTO dataset_row_value (dataset_id, dataset_row_number, column_id, value) VALUES (?, ?, ?, ?)",
        row_value_entries,
    )

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
                DatasetAccess(dataset_id=dataset.id, access_level=AccessLevel.CODE)
            )
            db.session.commit()
            return redirect(url_for("datasets.show_datasets"))
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
        return redirect(url_for("datasets.show_datasets"))

    return render_template(
        "view_dataset.html",
        dataset=dataset,
        **Type.export(),
        invite_link=dataset.generate_invite_link(
            request.host_url, current_app.encryption_key
        ),
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

    dataset = read_dataset(
        file, current_app.config["DATABASE_LOCATION"], description=description
    )

    if not dataset:
        flash("The uploaded file was malformed")
        return redirect(url_for("datasets.show_datasets"))

    current_user.dataset_rights.append(
        DatasetAccess(
            user_id=current_user.id,
            dataset_id=dataset.id,
            access_level=AccessLevel.ADMIN,
        )
    )

    project.datasets.append(dataset)
    db.session.commit()
    return redirect(url_for("projects.view_project", project_id=project_id))


@datasets.route("/dataset/update", methods=["POST"])
def update_dataset():
    dataset_id = request.form.get("dataset_id")
    dataset = Dataset.query.get(dataset_id)

    if not dataset:
        flash("The selected dataset doesn't exist")
        return redirect(url_for("datasets.show_datasets"))

    if not current_user.can_edit(dataset):
        flash("You do not have access to this dataset")
        return redirect(url_for("datasets.show_datasets"))

    for column in dataset.columns:
        datatype = request.form.get(column.name + "-type")
        prompt = request.form.get(column.name + "-prompt")
        order = request.form.get(column.name + "-order")
        if datatype:
            column.type = datatype
        if prompt or column.type == Type.HIDDEN:
            column.prompt = prompt
        if order and order.isdecimal():
            column.order = int(order)

    for index, column in enumerate(dataset.ordered_columns):
        column.order = index + 1

    db.session.commit()

    return redirect(url_for("datasets.view_dataset", dataset_id=dataset_id))


@datasets.route("/datasets", methods=["GET"])
def show_datasets():
    return render_template(
        "show_datasets.html", datasets=current_user.viewable_datasets()
    )


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

    row = DatasetRow.query.filter_by(
        dataset_id=dataset_id, coded=False, skip=False, post_unavailable=False
    ).first()

    if row:
        row = row.serialise()
    else:
        row = {"is_empty": True}

    return jsonify(row)


@datasets.route("/dataset/row", methods=["POST"])
def read_row():
    dataset_id = request.json["dataset_id"]
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        flash("The selected dataset doesn't exist")
        return redirect(url_for("datasets.view_datasets"))
    if not current_user.can_code(dataset):
        flash("You don't have access to this dataset")
        return redirect(url_for("datasets.view_datasets"))

    row_number = request.json["row_number"]
    if row_number.isdigit():
        row_number = int(row_number) - 1
    else:
        return {"is_empty": True}

    row = DatasetRow.query.filter_by(
        dataset_id=dataset_id, row_number=row_number
    ).first()

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

    row.skip = False
    row.post_unavailable = False
    row.coder = current_user

    if data.get("skip"):
        row.skip = True

    if data.get("post_unavailable"):
        row.post_unavailable = True

    values = []
    if "values" in data:
        values = data["values"].items()
        row.coded = True

    for (column_id, value) in values:
        row_value = DatasetRowValue.query.get((dataset_id, row_number, column_id))
        row_value.value = value

    db.session.commit()
    return next_row()


@datasets.route("/dataset/code/instagram/<dataset_id>/<row_number>/<column_id>")
def render_instagram(dataset_id, row_number, column_id):
    dataset = Dataset.query.get(dataset_id)
    if not dataset or not current_user.can_code(dataset):
        flash("You don't have access to that dataset")
        return redirect(url_for("show_datasets"))

    row_value = DatasetRowValue.query.get((dataset_id, row_number, column_id))

    return render_template("instagram_embed.html", url=row_value.value)


@datasets.route("/dataset/code/oembed/<dataset_id>/<row_number>/<column_id>")
def render_oembed(dataset_id, row_number, column_id):
    dataset = Dataset.query.get(dataset_id)
    if not dataset or not current_user.can_code(dataset):
        flash("You don't have access to that dataset")
        return redirect(url_for("show_datasets"))
    row_value = DatasetRowValue.query.get((dataset_id, row_number, column_id))

    url = row_value.value
    domain = requests.utils.urlparse(url).netloc

    print(
        f"https://{domain}/oembed?url={requests.utils.quote(url)}&maxwidth=800&maxheight=452"
    )
    response = requests.get(
        f"https://{domain}/oembed?url={requests.utils.quote(url)}&maxwidth=800&maxheight=452"
    )

    return jsonify(response.json())


@datasets.route("/dataset/delete", methods=["POST"])
def delete_dataset():
    dataset_id = request.form.get("dataset_id")
    confirm = (
        request.form.get("confirm") == "true"
    )  # Only if the confirm string is exactly "true"
    dataset = Dataset.query.get(dataset_id)

    if not confirm:
        return render_template("delete_dataset.html", dataset=dataset)
    else:
        if not dataset:
            return redirect(url_for("datasets.show_datasets"))
        if not current_user.can_edit(dataset):
            flash("You don't have access to this dataset")
            return redirect(url_for("datasets.show_datasets"))

        dataset = Dataset.query.get(dataset_id)
        db.session.delete(dataset)
        db.session.commit()

        return redirect(url_for("datasets.show_datasets"))


def dict_union(*dictionaries):
    result = {}
    for dictionary in dictionaries:
        result.update(dictionary)
    return result


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
            fieldnames=list(map(lambda column: column.name, dataset.columns))
            + [
                "coded",
                "post_unavailable",
                "skipped",
                "coder_username",
                "coder_firstname",
                "coder_surname",
                "coder_initials",
            ],
        )

        writer.writeheader()

        for row in dataset.rows:
            coder_initials = ""
            coder_username = ""
            coder_first_name = ""
            coder_surname = ""
            if row.coder is not None:
                coder_initials = row.coder.initials
                coder_username = row.coder.username
                coder_firstname = row.coder.firstname
                coder_surname = row.coder.surname

            writer.writerow(
                dict_union(
                    {entry.column.name: entry.value for entry in row.values},
                    {
                        "coder_initials": coder_initials,
                        "coder_username": coder_username,
                        "coder_firstname": coder_firstname,
                        "coder_surname": coder_surname,
                        "coded": row.coded,
                        "skipped": row.skip,
                        "post_unavailable": row.post_unavailable,
                    },
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
