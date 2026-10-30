FROM python:3.12-slim
WORKDIR /app
COPY calc.py .
CMD ["python", "-c", "import calc; print('calc ready:', calc.add(2, 3))"]