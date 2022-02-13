from flask import Flask
from flask_login import LoginManager
from app.database import db, User
from flask_migrate import Migrate
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

import os
import os.path
import json
import secrets

from app.views.authentication import authentication
from app.views.home import home
from app.views.projects import projects
from app.views.datasets import datasets


DATABASE_FILE_NAME= "db.sqlite3"

if not os.path.exists("config.json"):
    secret_key = secrets.token_urlsafe(64)
    with open("defaults/config.json") as file:
        config = json.load(file)
        config["secret-key"] = secret_key
    with open("config.json", "w") as file:
        json.dump(config, file, indent=2, sort_keys=True)
else:
    with open("config.json") as file:
        config = json.load(file)

app = Flask(__name__)

app.register_blueprint(home)
app.register_blueprint(authentication)
app.register_blueprint(projects)
app.register_blueprint(datasets)

DATABASE_LOCATION = os.path.join(app.instance_path, DATABASE_FILE_NAME)
DATABASE_URI = "sqlite:///" + DATABASE_LOCATION

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["DATABASE_LOCATION"] = DATABASE_LOCATION
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = config["secret-key"]

kdf = PBKDF2HMAC(
    algorithm=SHA256,
    length=32,
    salt=b"",
    iterations=390000
)

app.encryption_key = base64.urlsafe_b64encode(kdf.derive(app.secret_key.encode()))

login_manager = LoginManager()
login_manager.login_view = "authentication.login"
login_manager.init_app(app)

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

if __name__ == "__main__":
    app = create_app()
    app.run()
