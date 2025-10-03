#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Collect static files (CSS, JS, etc.)
python manage.py collectstatic --no-input

# 3. Apply database migrations
python manage.py migrate
