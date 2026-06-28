FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY services ./services
COPY eval ./eval
COPY sample_docs ./sample_docs

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

EXPOSE 8000

CMD ["fastapi", "run", "services/api/main.py", "--host", "0.0.0.0", "--port", "8000"]
