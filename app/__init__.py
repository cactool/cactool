from flask import Flask, render_template, request, flash, url_for, redirect
from passlib.hash import pbkdf2_sha256
from flask_login import LoginManager, login_user, current_user
from app.database import db, User
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
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
        return render_template("login.html")
 

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
        
        
        return render_template("signup.html")

if __name__ == "__main__":
    app = create_app() 
    app.run(debug=True)