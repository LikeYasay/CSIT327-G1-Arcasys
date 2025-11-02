#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing dependencies"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "==> Running database migrations"
python manage.py makemigrations
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Build complete"