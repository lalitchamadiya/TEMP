#!/usr/bin/env bash
# build.sh – Railway BUILD phase (no DATABASE_URL available here)
# collectstatic, migrate, and seeding all run in railway.toml [deploy] releaseCommand
set -o errexit

pip install -r requirements-prod.txt
python manage.py collectstatic --no-input
