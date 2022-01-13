from flask import Flask, render_template, request
from passlib.hash import pbkdf2_sha256
from database import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

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
        
        if pbkdf2_sha256.verify(password, user.password):
            return # TODO: Login
        else:
            return # TODO: Do not log in
 

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
            hashed_password = pbkdf2_sha256(password)
            user = User(username=username, password=hashed_password, firstname=firstname, surname=surname)
            db.session.add(user)
            db.session.commit()

            return # TODO: Some success
            
        else:
            return # TODO: Some error

if __name__ == "__main__":
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
