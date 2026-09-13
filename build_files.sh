#!/usr/bin/env bash
echo "Building Vercel project assets & database schema..."
python3 -m pip install --break-system-packages -r requirements.txt
python3 manage.py collectstatic --no-input --clear
python3 manage.py migrate --no-input || true
python3 manage.py seed_modules || true
python3 manage.py seed_super_admin || true
mkdir -p staticfiles
echo "Build complete."
