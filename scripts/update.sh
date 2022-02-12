#!/usr/bin/env bash
git pull
flask db upgrade
echo
echo "Successfully updated Cactool"