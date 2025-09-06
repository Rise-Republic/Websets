# syntax=docker/dockerfile:1

FROM python:3.13-slim AS build
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix /install --no-cache-dir -r requirements.txt

FROM python:3.13-slim
WORKDIR /app
RUN adduser --system --home /app --disabled-password appuser
COPY --from=build /install /usr/local
COPY app ./app
COPY alembic.ini .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
