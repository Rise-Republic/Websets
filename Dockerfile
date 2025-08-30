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
FROM python:3.13-slim AS backend-build
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Install Python dependencies without system packages to keep the build image small
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix /install --no-cache-dir -r requirements.txt \
    && pip install --prefix /install playwright

########## Final runtime stage ##########
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser \
    && apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip curl git \
    libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libgtk-3-0 libatspi2.0-0 libxrandr2 libasound2 libxdamage1 \
    libxss1 libgconf-2-4 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=backend-build /install /usr/local
# Install Playwright browser binaries
RUN playwright install-deps chromium && playwright install chromium
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser migrations ./migrations
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser --from=frontend-build /frontend/dist ./static
EXPOSE 8000
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
