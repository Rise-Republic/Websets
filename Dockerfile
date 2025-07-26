# syntax=docker/dockerfile:1

########## Frontend build stage ##########
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.ts tsconfig*.json postcss.config.js tailwind.config.js ./
COPY src ./src
RUN npm run build

########## Backend build stage ##########
FROM python:3.11-slim AS backend-build
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Install Python dependencies without system packages to keep the build image small
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix /install --no-cache-dir -r requirements.txt \
    && pip install --prefix /install playwright \
    && playwright install chromium

########## Final runtime stage ##########
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN adduser --system --home /app --disabled-password appuser
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip curl git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=backend-build /install /usr/local
# Install Playwright system dependencies and browser binaries
RUN playwright install-deps && playwright install chromium
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY --from=frontend-build /frontend/dist ./static
EXPOSE 8000
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
