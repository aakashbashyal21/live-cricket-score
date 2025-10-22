FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Use Uvicorn as entrypoint
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]