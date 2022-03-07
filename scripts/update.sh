#!/usr/bin/env bash

DIR=$1

echo Pulling latest software from GitHub...
git -C $DIR pull
echo Updating dependencies...
PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring pip install -Ur $DIR/requirements.txt --quiet
echo Upgrading database...
FLASK_APP=$DIR/app flask db upgrade
echo
echo "Successfully updated Cactool"
