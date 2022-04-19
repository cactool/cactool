import sys
import os
import os.path
import subprocess
import pathlib
import base64
import json
import secrets

import appdirs

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate, upgrade
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .database import db, AnonymousUser, User
from .views.authentication import authentication
from .views.home import home
from .views.projects import projects
from .views.datasets import datasets

import waitress

ROOT = pathlib.Path(__file__).parents[1]
CONFIG_DIR = appdirs.user_config_dir("cactool")
MIGRATIONS_DIR = os.path.join(ROOT, "cactool/migrations")
DEFAULT_CONFIG_FILE_NAME = os.path.join(ROOT, "cactool/defaults/config.json")
CONFIG_FILE_NAME = os.path.join(CONFIG_DIR, "config.json")
STARTUP_SCRIPT_LOCATION = os.path.join(ROOT, "cactool/bin/cactool")
STATIC_FOLDER_PATH = os.path.join(ROOT, "cactool/static")
DATABASE_FILE_NAME = "db.sqlite3"

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

if not os.path.exists(CONFIG_FILE_NAME):
    secret_key = secrets.token_urlsafe(64)
    with open(DEFAULT_CONFIG_FILE_NAME) as file:
        config = json.load(file)
        config["secret-key"] = secret_key
    with open(CONFIG_FILE_NAME, "w") as file:
        json.dump(config, file, indent=2, sort_keys=True)
else:
    with open(CONFIG_FILE_NAME) as file:
        config = json.load(file)

if not "upload-limit" in config:
    config["upload-limit"] = 1024
if not "max-rows" in config:
    config["max-rows"] = -1
if not "signup-code" in config or config["signup-code"] == "":
    config["signup-code"] = None

app = Flask(__name__, static_folder=STATIC_FOLDER_PATH)

app.register_blueprint(home)
app.register_blueprint(authentication)
app.register_blueprint(projects)
app.register_blueprint(datasets)

if not os.path.isdir(app.instance_path):
    try:
        os.makedirs(app.instance_path)
    except FileExistsError:
        pass

DATABASE_LOCATION = os.path.join(app.instance_path, DATABASE_FILE_NAME)
DATABASE_URI = "sqlite:///" + DATABASE_LOCATION

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["DATABASE_LOCATION"] = DATABASE_LOCATION
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = int(config["upload-limit"]) * 1024 ** 2
app.config["max_rows_in_memory"] = int(config["max-rows"])
app.config["signup-code"] = config["signup-code"]
app.secret_key = config["secret-key"]

kdf = PBKDF2HMAC(algorithm=SHA256, length=32, salt=b"", iterations=390000)

app.encryption_key = base64.urlsafe_b64encode(kdf.derive(app.secret_key.encode()))

login_manager = LoginManager()
login_manager.anonymous_user = AnonymousUser
login_manager.login_view = "authentication.login"
login_manager.init_app(app)

db.init_app(app)
migrate = Migrate(app, db, compare_type=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def get_value(key):
    if key == "port":
        if "port" in config:
            return config["port"]
        else:
            return 8080
    else:
        return config[key]


def write_config():
    with open(CONFIG_FILE_NAME, "w") as file:
        json.dump(config, file)


def set_value(key, value):
    config[key] = value
    write_config()


def unset_value(key):
    del config[key]
    write_config()


def upgrade_database():
    with app.app_context():
        upgrade(MIGRATIONS_DIR)


USAGE_STRING = """\
usage: cactool COMMAND [ARGS...]
Commands:
  cactool                   Starts the server
  cactool get NAME          Gets a configuration parameter
  cactool unset NAME        Unsets a configuration parameter
  cactool set NAME VALUE    Sets a configuration parameter\
"""


def cactool():
    if len(sys.argv) == 1:
        upgrade_database()
        bind = f"0.0.0.0:{get_value('port')}"
        print(f"Starting Cactool server instance at http://{bind}")
        waitress.serve(app, listen=bind)  # Start application
    elif len(sys.argv) == 2 and sys.argv[1] == "update":
        upgrade_database()  # Upgrade the database
    elif len(sys.argv) == 3 and sys.argv[1] == "get":
        print(get_value(sys.argv[2]))  # Get a configuration parameter
    elif len(sys.argv) == 3 and sys.argv[1] == "unset":
        unset_value(sys.argv[2])  # Unsets a configuration parameter
    elif len(sys.argv) == 4 and sys.argv[1] == "set":
        set_value(sys.argv[2], sys.argv[3])  # Sets a configuration parameter
    else:
        print(USAGE_STRING)
