FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY support_assistant ./support_assistant
COPY data ./data
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "support_assistant.api:app", "--host", "0.0.0.0", "--port", "8000"]