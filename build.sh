#!/usr/bin/env bash
# build.sh – Runs during Railway build phase
set -o errexit

pip install -r requirements-prod.txt
python manage.py collectstatic --no-input
python manage.py migrate
