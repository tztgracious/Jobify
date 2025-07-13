#!/bin/bash
# reset_db.sh

echo "🗑️  Clearing local database..."

# Remove SQLite database
if [ -f "db.sqlite3" ]; then
    rm db.sqlite3
    echo "✅ Removed db.sqlite3"
fi

# Remove migration files (keep __init__.py)
echo "🧹 Cleaning migration files..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Recreate migrations
echo "🔄 Creating fresh migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations resume

# Apply migrations
echo "📊 Applying migrations..."
python manage.py migrate

# Create superuser
echo "👤 Creating superuser..."
python manage.py createsuperuser

echo "🎉 Database reset complete!"
