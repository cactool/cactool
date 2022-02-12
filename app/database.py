from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import csv
import app.types as types
 
db = SQLAlchemy()


dataset_access = db.Table(
    "dataset_access",
    db.Column("user_id", db.ForeignKey("user.id")),
    db.Column("dataset_id", db.ForeignKey("dataset.id")),
    db.Column("access_level", db.Enum(types.AccessType))
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

    datasets = db.relationship("Dataset", secondary=dataset_access)
    projects = db.relationship("Project", secondary=project_access)

    def get_id(self):
        return self.id
    
    def initials(self):
        return self.firstname[0].upper() + self.surname[0].upper()
    
class Dataset(db.Model):
    id = db.Column(db.String(512), unique=True, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(1024))
    
    columns = db.relationship("DatasetColumn", cascade="all, delete-orphan")
    rows = db.relationship("DatasetRow", cascade="all, delete-orphan")

    projects = db.relationship("Project", secondary=project_datasets)
    users = db.relationship("User", secondary=dataset_access)
    
    def emit_csv(self) -> str:
        writer = csv.DictWriter()
        pass


class DatasetColumn(db.Model):
    id = db.Column(db.String(512), primary_key=True, unique=True) # Do I want a separate ID? (TODO)
    name = db.Column(db.String(50))
    type = db.Column(db.Enum(types.Type))
    dataset_id = db.Column(db.ForeignKey(Dataset.id))
    prompt = db.Column(db.String(512))

    dataset = db.relationship(Dataset, foreign_keys="DatasetColumn.dataset_id")
    
    
    # TODO: Unique (dataset, name) constraint 

class DatasetRow(db.Model):   
    dataset_id = db.Column(db.String(512), db.ForeignKey(Dataset.id), primary_key=True)
    row_number = db.Column(db.Integer, primary_key=True)

    coded = db.Column(db.Boolean())
    coder = db.Column(db.ForeignKey(User.id), nullable=True)
    
    skip = db.Column(db.Boolean())
    post_unavailable = db.Column(db.Boolean())

    values = db.relationship("DatasetRowValue", lazy=True, cascade="all, delete-orphan")
    dataset = db.relationship(Dataset, foreign_keys="DatasetRow.dataset_id")

    
    # no_load = FailToLoadReport User ids
    
    __table_args__ = (
        db.UniqueConstraint(dataset_id, row_number),
    )
    
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
                     "type": entry.column.type.serialise()
                }   for entry in self.values
            }
        }
    
    @staticmethod
    def empty(dataset_id, row_number):
        return {
            {
                
            }
        }


class DatasetRowValue(db.Model):
    dataset_id = db.Column(db.String(512), primary_key=True)
    dataset_row_number = db.Column(db.Integer, primary_key=True)
    column_id = db.Column(db.ForeignKey(DatasetColumn.id), primary_key=True)

    value = db.Column(db.String(65535))
    
    column = db.relationship("DatasetColumn")
    
    __table_args__ = (
        db.ForeignKeyConstraint(
            [dataset_id, dataset_row_number],
            [DatasetRow.dataset_id, DatasetRow.row_number]
        ),
        db.UniqueConstraint(
            dataset_id, dataset_row_number, column_id
        )
    )
    

class Project(db.Model):
    id = db.Column(db.String(512), primary_key=True, unique=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(1024))

    datasets = db.relationship("Dataset", secondary=project_datasets)
