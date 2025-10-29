#!/usr/bin/env bash
set -o errexit

# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate