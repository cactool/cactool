from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin
import csv
from .types import Type, AccessLevel
import cryptography.fernet
 
db = SQLAlchemy()


class AccessContainer:
    def grants(self, access_type, thing=False):
        return (not thing or self.container_id == thing.id) and access_type <= self.access_level

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

class DatasetAccess(db.Model, AccessContainer):
    user_id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    dataset_id = db.Column(db.ForeignKey("dataset.id"), primary_key=True)
    access_level = db.Column(db.Enum(AccessLevel))
    
    dataset = db.relationship("Dataset")
    
    @property
    def container_id(self):
        return self.dataset_id

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
    db.Column("dataset_id", db.ForeignKey("dataset.id"))
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

    def initials(self):
        return "??"

class User(UserMixin, db.Model):
    id = db.Column(db.String(512), unique=True, primary_key=True)
    admin = db.Column(db.Boolean)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(1024))
    firstname = db.Column(db.String(50))
    surname = db.Column(db.String(50))

    dataset_rights = db.relationship(DatasetAccess)
    project_rights = db.relationship(ProjectAccess)
    

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
       return self.can(
           AccessLevel.ADMIN,
           thing 
       )

    def can_export(self, thing):
        return self.can(
            AccessLevel.EXPORT,
            thing 
        )
        
    def can_code(self, thing):
        return self.can(
            AccessLevel.CODE,
            thing
        )


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
        return DatasetRow.query.filter_by(
            dataset_id=self.id
        ).count()
    
    @property
    def ordered_columns(self):
        return sorted(self.columns, key=lambda column: column.type != Type.SOCIAL_MEDIA)


class DatasetColumn(db.Model):
    id = db.Column(db.String(512), primary_key=True, unique=True)
    name = db.Column(db.String(50))
    type = db.Column(db.Enum(Type))
    dataset_id = db.Column(db.ForeignKey(Dataset.id))
    prompt = db.Column(db.String(512))

    dataset = db.relationship(Dataset, foreign_keys="DatasetColumn.dataset_id")
    
    
    __table_args__ = (
        db.UniqueConstraint(dataset_id, name),
    )

class DatasetRow(db.Model):   
    dataset_id = db.Column(db.String(512), db.ForeignKey(Dataset.id), primary_key=True)
    row_number = db.Column(db.Integer, primary_key=True)

    coded = db.Column(db.Boolean())
    coder_id = db.Column(db.ForeignKey(User.id), nullable=True)
    
    skip = db.Column(db.Boolean())
    post_unavailable = db.Column(db.Boolean())

    values = db.relationship("DatasetRowValue", lazy=True, cascade="all, delete-orphan")
    dataset = db.relationship(Dataset, foreign_keys="DatasetRow.dataset_id")
    
    coder = db.relationship("User", foreign_keys="DatasetRow.coder_id")
    
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
