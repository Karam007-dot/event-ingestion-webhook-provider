#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "PostgreSQL started successfully."

cd /app/core
python manage.py makemigrations
python manage.py migrate

exec "$@"