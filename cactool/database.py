import base64
import csv
import operator
import secrets

import cryptography.fernet
from flask_login import AnonymousUserMixin, UserMixin
from flask_sqlalchemy import SQLAlchemy

from .types import AccessLevel, Type

db = SQLAlchemy()


class AccessContainer:
    def grants(self, access_type, thing=False):
        return (
            not thing or self.container_id == thing.id
        ) and access_type <= self.access_level

    def grant_condition(self, access_type):
        def condition(thing):
            return self.grants(access_type, thing)

        return condition

    @property
    def access_level(self):
        raise NotImplementedError()

    @property
    def container_id(self):
        raise NotImplementedError()


class UserEmailVerification(db.Model):
    verification_code = db.Column(db.String(16), primary_key=True)
    user_id = db.Column(db.ForeignKey("user.id"))
    timestamp = db.Column(db.Integer())


class DatasetAccess(db.Model, AccessContainer):
    user_id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    dataset_id = db.Column(db.ForeignKey("dataset.id"), primary_key=True)
    access_level = db.Column(db.Enum(AccessLevel))

    @property
    def container_id(self):
        return self.dataset_id

    dataset = db.relationship("Dataset")


class ProjectAccess(db.Model, AccessContainer):
    user_id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    project_id = db.Column(db.ForeignKey("project.id"), primary_key=True)
    access_level = db.Column(db.Enum(AccessLevel))

    @property
    def container_id(self):
        return self.project_id


project_datasets = db.Table(
    "project_datasets",
    db.Column("project_id", db.ForeignKey("project.id")),
    db.Column("dataset_id", db.ForeignKey("dataset.id")),
)


class AnonymousUser(AnonymousUserMixin):
    def viewable_datasets(self):
        return []

    def editable_projects(self):
        return []

    def can(self, access_type, thing):
        return False

    def can_dataset(self, dataset, access_type):
        return False

    def can_project(self, project, access_type):
        return False

    def can_edit(self, thing):
        return False

    def can_code(self, thing):
        return False

    def can_export(self, thing):
        return False

    @property
    def initials(self):
        return "??"


class User(UserMixin, db.Model):
    id = db.Column(db.String(512), unique=True, primary_key=True)
    admin = db.Column(db.Boolean)
    username = db.Column(db.String(20), unique=True)
    otp_secret = db.Column(db.String())
    email = db.Column(db.String(50))
    password = db.Column(db.String(1024))
    firstname = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    unverified = db.Column(db.Boolean(), default=False)

    dataset_rights = db.relationship(DatasetAccess)
    project_rights = db.relationship(ProjectAccess)
    email_verification = db.relationship(UserEmailVerification)

    def viewable_datasets(self):
        datasets = []
        for access in self.dataset_rights:
            if access.grants(AccessLevel.CODE):
                datasets.append(access.dataset)

        return datasets

    def editable_projects(self):
        projects = []
        for access in self.project_rights:
            project = Project.query.get(access.project_id)
            if project and self.can_edit(project):
                projects.append(project)

        return projects

    def can(self, access_type, thing):
        if isinstance(thing, Dataset):
            return self.can_dataset(thing, access_type)

        if isinstance(thing, Project):
            return self.can_project(thing, access_type)

        raise TypeError("User.can expects an instance of Project or Dataset")

    def can_dataset(self, dataset, access_type):
        rights = DatasetAccess.query.get((self.id, dataset.id))
        return rights and rights.grants(access_type, dataset)

    def can_project(self, project, access_type):
        rights = ProjectAccess.query.get((self.id, project.id))
        return rights and rights.grants(access_type, project)

    def can_edit(self, thing):
        return self.can(AccessLevel.ADMIN, thing)

    def can_export(self, thing):
        return self.can(AccessLevel.EXPORT, thing)

    def can_code(self, thing):
        return self.can(AccessLevel.CODE, thing)

    def get_id(self):
        return self.id

    @property
    def initials(self):
        return self.firstname[0].upper() + self.surname[0].upper()

    def regenerate_otp_secret(self):
        self.otp_secret = User.random_otp_secret()

    @staticmethod
    def random_otp_secret():
        byte_sequence = secrets.token_bytes(40)
        return base64.b32encode(byte_sequence).decode()

    @staticmethod
    def otp_secret_to_url(secret, username=None):
        if username:
            return f"otpauth://totp/Cactool:{username}?secret={secret}&issuer=Cactool"
        return f"otpauth://totp/Cactool?secret={secret}"

    @property
    def has_2fa(self):
        return self.otp_secret is not None

    def disable_2fa(self):
        self.otp_secret = None

    @property
    def otp_secret_url(self):
        if not self.otp_secret:
            return None
        return User.otp_secret_to_url(self.otp_secret, username=self.username)


class Dataset(db.Model):
    id = db.Column(db.String(512), unique=True, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(1024))

    columns = db.relationship("DatasetColumn", cascade="all, delete-orphan")
    rows = db.relationship("DatasetRow", cascade="all, delete-orphan")

    projects = db.relationship("Project", secondary=project_datasets)

    granted_access = db.relationship("DatasetAccess", cascade="all, delete-orphan")

    def emit_csv(self) -> str:
        writer = csv.DictWriter()
        pass

    def confirm(self, code, ekey):
        fernet = cryptography.fernet.Fernet(ekey)
        return fernet.decrypt(code) == self.id.encode()

    def code(self, ekey):
        fernet = cryptography.fernet.Fernet(ekey)
        return fernet.encrypt(self.id.encode()).hex()

    def generate_invite_link(self, base_url, ekey):
        return base_url + f"dataset/invite/{self.id}/{self.code(ekey)}"

    @property
    def num_rows(self):
        return DatasetRow.query.filter_by(dataset_id=self.id).count()

    @property
    def num_coded(self):
        return DatasetRow.query.filter_by(
            dataset_id=self.id, coded=True, skip=False
        ).count()

    @property
    def num_skipped(self):
        return DatasetRow.query.filter_by(dataset_id=self.id, skip=True).count()

    @property
    def num_unavailable(self):
        return DatasetRow.query.filter_by(
            dataset_id=self.id, post_unavailable=True
        ).count()

    @property
    def code_status_description(self):
        messages = [f"{self.num_coded} coded"]

        num_skipped = self.num_skipped
        num_unavailable = self.num_unavailable
        if num_skipped:
            messages.append(f"{num_skipped} skipped")
        if num_unavailable:
            messages.append(f"{num_unavailable} unavailable")

        return ", ".join(messages)

    @property
    def ordered_columns(self):
        return sorted(self.columns, key=lambda column: column.order or 999)


class DatasetColumn(db.Model):
    id = db.Column(db.String(512), primary_key=True, unique=True)
    name = db.Column(db.String(50))
    type = db.Column(db.Enum(Type))
    dataset_id = db.Column(db.ForeignKey(Dataset.id))
    prompt = db.Column(db.String(512))
    order = db.Column(db.Integer, default=999)

    dataset = db.relationship(Dataset, foreign_keys="DatasetColumn.dataset_id")

    __table_args__ = (db.UniqueConstraint(dataset_id, name),)


class DatasetRow(db.Model):
    dataset_id = db.Column(db.String(512), db.ForeignKey(Dataset.id), primary_key=True)
    row_number = db.Column(db.Integer, primary_key=True)

    coded = db.Column(db.Boolean(), default=False)
    coder_id = db.Column(db.ForeignKey(User.id), nullable=True)

    skip = db.Column(db.Boolean(), default=False)
    post_unavailable = db.Column(db.Boolean(), default=False)

    values = db.relationship("DatasetRowValue", lazy=True, cascade="all, delete-orphan")
    dataset = db.relationship(Dataset, foreign_keys="DatasetRow.dataset_id")

    coder = db.relationship("User", foreign_keys="DatasetRow.coder_id")

    __table_args__ = (db.UniqueConstraint(dataset_id, row_number),)

    def serialise(self):
        return {
            "is_empty": False,
            "dataset_id": self.dataset_id,
            "row_number": self.row_number,
            "columns": {
                entry.column.id: {
                    "name": entry.column.name,
                    "prompt": entry.column.prompt,
                    "value": entry.value,
                    "type": entry.column.type.serialise(),
                }
                for entry in sorted(
                    self.values, key=lambda value: value.column.order or 0
                )
            },
        }

    @staticmethod
    def empty(dataset_id, row_number):
        return {{}}


class DatasetRowValue(db.Model):
    dataset_id = db.Column(db.String(512), primary_key=True)
    dataset_row_number = db.Column(db.Integer, primary_key=True)
    column_id = db.Column(db.ForeignKey(DatasetColumn.id), primary_key=True)

    value = db.Column(db.String(65535))

    column = db.relationship("DatasetColumn")

    __table_args__ = (
        db.ForeignKeyConstraint(
            [dataset_id, dataset_row_number],
            [DatasetRow.dataset_id, DatasetRow.row_number],
        ),
        db.UniqueConstraint(dataset_id, dataset_row_number, column_id),
    )


class Project(db.Model):
    id = db.Column(db.String(512), primary_key=True, unique=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(1024))

    datasets = db.relationship("Dataset", secondary=project_datasets)
