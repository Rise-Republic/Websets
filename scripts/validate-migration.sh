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
