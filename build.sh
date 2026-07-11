#!/usr/bin/env bash
# build.sh – Runs during Railway BUILD phase (no DB access here)
# All DB operations (migrate, seed) are in railway.toml [deploy] releaseCommand
set -o errexit

pip install -r requirements-prod.txt
python manage.py collectstatic --no-input
