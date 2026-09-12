#!/usr/bin/env bash
echo "Building Vercel project assets..."
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --no-input --clear
echo "Build complete."
