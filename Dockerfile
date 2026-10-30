FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN gunicorn --version
COPY calc.py app.py ./
RUN useradd --create-home appuser
USER appuser
ARG BUILD_ID=local
ENV BUILD_ID=$BUILD_ID
LABEL org.opencontainers.image.source="https://github.com/<your-username>/action-practice"
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]