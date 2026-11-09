FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN gunicorn --version
RUN python -c "import confluent_kafka"
COPY calc.py app.py worker.py ./
RUN useradd --create-home appuser
USER appuser
ARG BUILD_ID=local
ENV BUILD_ID=$BUILD_ID
LABEL org.opencontainers.image.source="https://github.com/mierule7/action-practice"
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--worker-class", "gthread", "--workers", "1", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "app:app"]