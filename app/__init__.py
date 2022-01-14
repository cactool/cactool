from flask import Flask, render_template, request
from passlib.hash import pbkdf2_sha256
import uuid
from flask_login import LoginManager
from app.database import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

db.init_app(app)
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        
        user = User.query.filter_by(username=username).first()

        if not user:
            return "user doesn't exist" # TODO: Error, user doesn't exist
        if pbkdf2_sha256.verify(password, user.password):
            return "success" # TODO: Login
        else:
            return "wrong password" # TODO: Do not log in
 

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
            return #TODO: error

        if username and password and firstname and surname:
            hashed_password = pbkdf2_sha256.hash(password)
            user = User(
                username=username,
                password=hashed_password,
                firstname=firstname,
                surname=surname,
                ID=uuid.uuid4().hex
            )
            db.session.add(user)
            db.session.commit()

            return "success" # TODO: Some success
            
        else:
            return "some fields left blank" # TODO: Some error

if __name__ == "__main__":
    app = create_app() 
    app.run(debug=True)
