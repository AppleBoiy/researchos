#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Flask application..."
exec flask --app "app:create_app()" run --host 0.0.0.0 --port 5000 --reload
