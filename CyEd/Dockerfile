# CyEd backend image.
# Build from the REPO ROOT (D:/cybercom) so the shared platform/ + shared/ are in
# the context:   docker build -f CyEd/Dockerfile -t cyed-api .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# System deps for psycopg + cryptography.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY CyEd/requirements.txt /app/CyEd/requirements.txt
RUN pip install --no-cache-dir -r /app/CyEd/requirements.txt

# Shared platform packages (must sit next to CyEd at the repo root).
COPY platform/ /app/platform/
COPY shared/ /app/shared/
COPY CyEd/ /app/CyEd/

WORKDIR /app/CyEd
ENV DJANGO_SETTINGS_MODULE=core.settings

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000
# Migrate on boot, then serve via gunicorn (WSGI does the platform namespace graft).
CMD sh -c "python manage.py migrate --noinput && \
    gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --timeout 60"
