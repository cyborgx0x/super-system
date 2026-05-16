FROM python:3.12-alpine
WORKDIR /app
COPY super-system/pyproject.toml /app/pyproject.toml
COPY super-system/backend /app/backend
RUN pip install --no-cache-dir django djangorestframework
EXPOSE 8088
CMD ["sh", "-c", "python /app/backend/manage.py migrate --noinput && python /app/backend/manage.py seed && python /app/backend/manage.py runserver 0.0.0.0:8088"]
