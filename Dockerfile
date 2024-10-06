FROM python:3.9-slim-buster
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
ENV FLASK_ENV=prod
ENV PORT=5000
ENV MOZ_HEADLESS=1
EXPOSE 5000
CMD gunicorn --bind 0.0.0.0:${PORT} \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --timeout 300 \
    -k gthread \
    --thread=3 \
    "app:create_app()"