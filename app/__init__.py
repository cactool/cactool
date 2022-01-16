from flask import Flask, render_template, request, flash, url_for, redirect
from passlib.hash import pbkdf2_sha256
from flask_login import LoginManager, login_user, current_user
from app.database import db, User, Project, project_access, Dataset, DatasetColumn, DatasetRow, DatasetRowValue
import app.types as types
from werkzeug.utils import secure_filename
import uuid
import csv
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "development" # TODO: ????

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

db.init_app(app)
with app.app_context():
    db.create_all()

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

    
    

def read_dataset(file):
    reader = csv.reader(file.read().decode().splitlines())
    
    
    date_string = datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")

    dataset = Dataset(
        id = uuid.uuid4().hex,
        name = secure_filename(file.filename),
        description = f"Uploaded {date_string}" 
    )
    

    columns = next(reader) # TODO: Consider case when file is nefariously empty
    for column in columns:
        column = DatasetColumn(
            id = uuid.uuid4().hex,
            type = types.Type.STRING,
            name = column
        )
        dataset.columns.append(column)
        db.session.add(column)
    
    db.session.add(dataset)
    db.session.commit()
      
    return dataset

@app.route("/dataset/import", methods=["POST", "GET"])
def import_dataset():
    if not current_user.is_authenticated:
        flash("Please log in to perform this action") 
        return redirect(url_for("login"))
    if request.method == "GET":
        return render_template("import_dataset.html")
    
    # Check None (TODO)
    print(request.files)
    file = request.files.get("file")
    if not file:
        flash("Please submit a file") # TODO: Error
        return render_template("import_dataset.html")
    
    dataset = read_dataset(file)
    current_user.datasets.append(dataset)
    db.session.commit()
    print(current_user.datasets)
    print("append")
    return render_template("import_dataset.html")

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
    
    project = Project(
        id = uuid.uuid4().hex,
        name = name        
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
            login_user(user)
            flash("Logged in successfully")
        else:
            flash("You enterred the wrong password for this account")
            
        
        return redirect(url_for("dashboard")) 
 

@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
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
            hashed_password = pbkdf2_sha256.hash(password)
            user = User(
                username=username,
                password=hashed_password,
                firstname=firstname,
                surname=surname,
                id=uuid.uuid4().hex
            )
            db.session.add(user)
            db.session.commit()

            flash("Successfilly created an account")
            
        else:
            flash("Some fields were left blank")
        
        
        return redirect(url_for("login")) 

if __name__ == "__main__":
    app = create_app() 
    app.run(debug=True)