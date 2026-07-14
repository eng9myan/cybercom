#!/bin/sh
set -e

if [ -n "$DB_HOST" ] && [ "${USE_SQLITE:-False}" != "True" ]; then
  echo "Waiting for postgres at $DB_HOST:${DB_PORT:-5432}..."
  until pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" >/dev/null 2>&1; do
    sleep 1
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn core_project.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
