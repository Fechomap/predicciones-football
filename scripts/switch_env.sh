#!/bin/bash

# Script para cambiar entre entornos (development/production)

if [ "$1" == "dev" ] || [ "$1" == "development" ]; then
    echo "🔧 Cambiando a DESARROLLO (local database)..."
    sed -i '' 's/^ENVIRONMENT=.*/ENVIRONMENT=development/' .env
    
    # Get local database URL
    LOCAL_DB=$(grep "^DATABASE_URL_LOCAL=" .env | cut -d'=' -f2)
    if [ ! -z "$LOCAL_DB" ]; then
        sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=$LOCAL_DB|" .env
    fi
    
    echo "✅ Entorno: DEVELOPMENT"
    echo "📚 Database: $LOCAL_DB"
    
elif [ "$1" == "prod" ] || [ "$1" == "production" ]; then
    echo "🚀 Cambiando a PRODUCCIÓN (Railway database)..."
    sed -i '' 's/^ENVIRONMENT=.*/ENVIRONMENT=production/' .env
    
    # Get production database URL
    PROD_DB=$(grep "^DATABASE_URL_PRODUCTION=" .env | cut -d'=' -f2)
    if [ ! -z "$PROD_DB" ]; then
        sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=$PROD_DB|" .env
    fi
    
    echo "✅ Entorno: PRODUCTION"
    echo "📚 Database: Railway PostgreSQL"
    
else
    echo "❌ Uso: ./switch_env.sh [dev|prod]"
    echo ""
    echo "Ejemplos:"
    echo "  ./switch_env.sh dev   # Usar base de datos local"
    echo "  ./switch_env.sh prod  # Usar base de datos Railway"
    exit 1
fi

echo ""
echo "⚠️  Reinicia el bot para aplicar los cambios"
