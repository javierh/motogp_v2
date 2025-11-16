#!/bin/bash

# NovaPorra Quick Start Script
# Este script facilita el primer setup del proyecto

set -e

echo "🏍️  NovaPorra - Setup Inicial"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose no está instalado"
    exit 1
fi

echo "✅ Docker y Docker Compose detectados"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde .env.example..."
    cp .env.example .env
    
    echo ""
    echo "⚠️  IMPORTANTE: Debes configurar las siguientes variables en .env:"
    echo "   - TELEGRAM_BOT_TOKEN (obtener de @BotFather)"
    echo "   - MYSQL_PASSWORD"
    echo "   - MYSQL_ROOT_PASSWORD"
    echo ""
    read -p "¿Deseas editar .env ahora? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    else
        echo "Recuerda editar .env antes de continuar:"
        echo "  nano .env"
        exit 0
    fi
else
    echo "✅ Archivo .env encontrado"
fi

echo ""
echo "🔨 Construyendo imágenes Docker..."
docker-compose build

echo ""
echo "🚀 Iniciando servicios..."
docker-compose up -d

echo ""
echo "⏳ Esperando que MySQL esté listo..."
sleep 10

# Wait for MySQL to be ready
until docker-compose exec -T mysql mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} --silent 2>/dev/null; do
    echo "Esperando MySQL..."
    sleep 2
done

echo "✅ MySQL está listo"

echo ""
read -p "¿Deseas crear datos de prueba? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📊 Creando datos de prueba..."
    docker-compose exec bot python -m src.utils.admin_scripts create_test_data
fi

echo ""
echo "✅ ¡Setup completado!"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Busca tu bot en Telegram"
echo "   2. Envía /start para registrarte"
echo "   3. Usa /ayuda para ver comandos"
echo "   4. Prueba /apostar para crear una apuesta"
echo ""
echo "🔧 Comandos útiles:"
echo "   Ver logs:     docker-compose logs -f bot"
echo "   Detener:      docker-compose down"
echo "   Reiniciar:    docker-compose restart"
echo ""
echo "📚 Documentación:"
echo "   Setup:        cat SETUP.md"
echo "   Técnica:      cat TECHNICAL.md"
echo ""
