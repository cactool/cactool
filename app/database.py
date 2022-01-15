from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import app.types as types
 
db = SQLAlchemy()


dataset_access = db.Table(
    "dataset_access",
    db.Column("user_id", db.ForeignKey("user.id")),
    db.Column("dataset_id", db.ForeignKey("dataset.id"))
)

project_datasets = db.Table(
    "project_datasets",
    db.Column("project_id", db.ForeignKey("project.id")),
    db.Column("dataset_id", db.ForeignKey("dataset.id"))
)

project_access = db.Table(
    "project_access",
    db.Column("user_id", db.ForeignKey("user.id")),
    db.Column("project_id", db.ForeignKey("project.id"))
)


class User(UserMixin, db.Model):
    id = db.Column(db.String(512), unique=True, primary_key=True)
    admin = db.Column(db.Boolean)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(1024))
    firstname = db.Column(db.String(50))
    surname = db.Column(db.String(50))

    def get_id(self):
        return self.ID
    
    datasets = db.relationship("Dataset", secondary=dataset_access)
    projects = db.relationship("Project", secondary=project_access)

    def get_id(self):
        return self.id
    
class Dataset(db.Model):
    id = db.Column(db.String(512), unique=True, primary_key=True)
    name = db.Column(db.String(50))
    
    rows = db.relationship("DatasetRow", lazy=True)

    projects = db.relationship("Project", secondary=project_datasets)
    users = db.relationship("User", secondary=dataset_access)


class DatasetColumn(db.Model):
    id = db.Column(db.String(512), primary_key=True, unique=True) # Do I want a separate ID? (TODO)
    type = db.Column(db.Enum(types.Type))

class DatasetRow(db.Model):   
    dataset_id = db.Column(db.String(512), db.ForeignKey(Dataset.id), primary_key=True)
    row_number = db.Column(db.Integer, primary_key=True)

    values = db.relationship("DatasetRowValue", lazy=True)
    dataset = db.relationship(Dataset, foreign_keys="DatasetRow.dataset_id")
    
    __table_args__ = (
        db.UniqueConstraint(dataset_id, row_number),
    )

class DatasetRowValue(db.Model):
    dataset_id = db.Column(db.String(512), primary_key=True)
    dataset_row_number = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, primary_key=True)

    value = db.Column(db.String(65535), primary_key=True)
    
    __table_args__ = (
        db.ForeignKeyConstraint(
            [dataset_id, dataset_row_number],
            [DatasetRow.dataset_id, DatasetRow.row_number]
        ),
        db.UniqueConstraint(
            dataset_id, dataset_row_number, index
        )
    )
    

class Project(db.Model):
    id = db.Column(db.String(512), primary_key=True, unique=True)
    name = db.Column(db.String(50))

    datasets = db.relationship("Dataset", secondary=project_datasets)
