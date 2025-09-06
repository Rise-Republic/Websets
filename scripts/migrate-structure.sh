#!/bin/bash
# WebSets Repository Structure Migration Script
# Phase 3: Core Application Migration

set -e

echo "🚀 Starting WebSets repository structure migration..."

# Create backup of current state
echo "📦 Creating backup..."
git add -A
git commit -m "backup: pre-migration state" || echo "No changes to commit"

# Validation function
validate_file_exists() {
    if [ ! -e "$1" ]; then
        echo "❌ Error: $1 does not exist"
        exit 1
    fi
}

# Phase 3.3: Frontend Migration
echo "🎨 Migrating frontend application to apps/web-ui/..."

# Validate source files exist
validate_file_exists "src"
validate_file_exists "package.json"
validate_file_exists "index.html"

# Move frontend files
cp -r src/ apps/web-ui/src/
cp package.json apps/web-ui/
cp package-lock.json apps/web-ui/
cp index.html apps/web-ui/
cp vite.config.ts apps/web-ui/
cp tailwind.config.js apps/web-ui/
cp postcss.config.js apps/web-ui/
cp tsconfig*.json apps/web-ui/
cp jest.config.js apps/web-ui/ 2>/dev/null || echo "jest.config.js not found, skipping"
cp playwright.config.ts apps/web-ui/ 2>/dev/null || echo "playwright.config.ts not found, skipping"

echo "✅ Frontend files copied to apps/web-ui/"

# Phase 3.4: Backend Migration
echo "🔧 Migrating backend API to apps/api-gateway/..."

# Validate backend files exist
validate_file_exists "app"
validate_file_exists "requirements.txt"

# Move backend files
cp -r app/ apps/api-gateway/app/
cp requirements.txt apps/api-gateway/
cp requirements-dev.txt apps/api-gateway/ 2>/dev/null || echo "requirements-dev.txt not found, skipping"
cp alembic.ini apps/api-gateway/ 2>/dev/null || echo "alembic.ini not found, skipping"

echo "✅ Backend files copied to apps/api-gateway/"

# Database migration
echo "🗄️ Migrating database files to db/..."
if [ -d "migrations" ]; then
    cp -r migrations/ db/migrations/
    echo "✅ Database migrations copied to db/migrations/"
fi

# Create service-specific Dockerfiles
echo "🐳 Creating service-specific Dockerfiles..."

# Frontend Dockerfile
cat > apps/web-ui/Dockerfile << 'EOF'
# syntax=docker/dockerfile:1

FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1
EOF

# Backend Dockerfile
cat > apps/api-gateway/Dockerfile << 'EOF'
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
EOF

echo "✅ Service-specific Dockerfiles created"

# Create nginx config for frontend
cat > apps/web-ui/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api {
            proxy_pass http://api-gateway:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF

echo "✅ Nginx configuration created for frontend"

# Create validation script
cat > scripts/validate-migration.sh << 'EOF'
#!/bin/bash
echo "🔍 Validating migration..."

# Check if new structure exists
for dir in apps/web-ui apps/api-gateway db/migrations; do
    if [ ! -d "$dir" ]; then
        echo "❌ Missing directory: $dir"
        exit 1
    fi
done

# Check if key files exist
if [ ! -f "apps/web-ui/package.json" ]; then
    echo "❌ Missing apps/web-ui/package.json"
    exit 1
fi

if [ ! -f "apps/api-gateway/requirements.txt" ]; then
    echo "❌ Missing apps/api-gateway/requirements.txt"
    exit 1
fi

echo "✅ Migration validation passed"
EOF

chmod +x scripts/validate-migration.sh

echo "🎉 Migration script completed successfully!"
echo "📋 Next steps:"
echo "  1. Run validation: ./scripts/validate-migration.sh"
echo "  2. Test builds in new structure"
echo "  3. Update import paths and configurations"
