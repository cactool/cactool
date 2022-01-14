from flask import Flask, render_template, request, flash
from passlib.hash import pbkdf2_sha256
import uuid
from flask_login import LoginManager, login_user
from app.database import db, User

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
    return render_template("index.html")


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
            flash("User doesn't exist") # TODO: Error, user doesn't exist
        elif pbkdf2_sha256.verify(password, user.password):
            login_user(user) # TODO: Check remember
            flash("Logged in successfully") # TODO: Login
        else:
            flash("wrong password") # TODO: Do not log in
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
            flash("user already exists with this username") #TODO: error

        elif username and password and firstname and surname:
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

            flash("success") # TODO: Some success
            
        else:
            flash("some fields left blank") # TODO: Some error
        
        
        return render_template("signup.html")

if __name__ == "__main__":
    app = create_app() 
    app.run(debug=True)
