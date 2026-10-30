FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY calc.py app.py ./
ARG BUILD_ID=local
ENV BUILD_ID=$BUILD_ID
LABEL org.opencontainers.image.source="https://github.com/mierule7/action-practice"
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]