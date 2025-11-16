#!/bin/bash
# Installation script for LXC container
# Run as root or with sudo

set -e

echo "🏍️  NovaPorra - Instalación para LXC"
echo "====================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Este script debe ejecutarse como root"
    echo "Usa: sudo bash install_lxc.sh"
    exit 1
fi

# Update system
echo "📦 Actualizando sistema..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "📦 Instalando dependencias..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    mysql-server \
    git \
    curl \
    vim \
    htop

# Create app user
echo "👤 Creando usuario de aplicación..."
if ! id -u novaporra > /dev/null 2>&1; then
    useradd -m -s /bin/bash novaporra
    echo "Usuario 'novaporra' creado"
else
    echo "Usuario 'novaporra' ya existe"
fi

# Create app directory
APP_DIR="/opt/novaporra"
echo "📁 Creando directorio de aplicación: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or copy repository
if [ -d ".git" ]; then
    echo "📥 Actualizando repositorio..."
    sudo -u novaporra git pull
else
    echo "📥 Clonando repositorio..."
    # Si ya tienes los archivos, cópialos aquí
    # O clona desde git cuando lo tengas en un repo
    cp -r /tmp/novaporra/* . 2>/dev/null || true
fi

# Set permissions
chown -R novaporra:novaporra $APP_DIR

# Setup Python virtual environment
echo "🐍 Configurando entorno virtual Python..."
sudo -u novaporra python3 -m venv $APP_DIR/venv

# Install Python dependencies
echo "📦 Instalando dependencias Python..."
sudo -u novaporra $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u novaporra $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Configure MySQL
echo "🗄️  Configurando MySQL..."
systemctl start mysql
systemctl enable mysql

# Secure MySQL installation
echo "Configurando seguridad de MySQL..."
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'CHANGE_THIS_ROOT_PASSWORD';" || true

# Create database and user
echo "Creando base de datos y usuario..."
MYSQL_ROOT_PASS="CHANGE_THIS_ROOT_PASSWORD"
DB_NAME="novaporra"
DB_USER="novaporra_user"
DB_PASS="CHANGE_THIS_DB_PASSWORD"

mysql -u root -p"$MYSQL_ROOT_PASS" <<MYSQL_SCRIPT
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
MYSQL_SCRIPT

# Initialize database
echo "📊 Inicializando base de datos..."
mysql -u root -p"$MYSQL_ROOT_PASS" $DB_NAME < $APP_DIR/migrations/init.sql

# Setup environment file
echo "⚙️  Configurando variables de entorno..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > $APP_DIR/.env <<EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=$DB_NAME
MYSQL_USER=$DB_USER
MYSQL_PASSWORD=$DB_PASS

# MotoGP API Configuration (not needed for public API)
MOTOGP_API_URL=https://api.motogp.pulselive.com/motogp/v1
MOTOGP_API_KEY=
MOTOGP_API_SECRET=

# Application Configuration
APP_TIMEZONE=Europe/Madrid
BET_CLOSE_MINUTES=10
CURRENT_SEASON=2024

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/novaporra.log

# Development
DEBUG=False
EOF
    chown novaporra:novaporra $APP_DIR/.env
    chmod 600 $APP_DIR/.env
    
    echo "⚠️  IMPORTANTE: Edita $APP_DIR/.env y configura tu TELEGRAM_BOT_TOKEN"
fi

# Create logs directory
mkdir -p $APP_DIR/logs
chown novaporra:novaporra $APP_DIR/logs

# Create systemd service
echo "🔧 Creando servicio systemd..."
cat > /etc/systemd/system/novaporra.service <<EOF
[Unit]
Description=NovaPorra MotoGP Betting Bot
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=novaporra
Group=novaporra
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python -m src.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo ""
echo "✅ Instalación completada!"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Editar configuración:"
echo "   sudo nano $APP_DIR/.env"
echo "   (Configura tu TELEGRAM_BOT_TOKEN)"
echo ""
echo "2. Sincronizar datos de MotoGP:"
echo "   sudo -u novaporra $APP_DIR/venv/bin/python $APP_DIR/scripts/sync_data.py"
echo ""
echo "3. Iniciar el servicio:"
echo "   sudo systemctl start novaporra"
echo ""
echo "4. Habilitar inicio automático:"
echo "   sudo systemctl enable novaporra"
echo ""
echo "5. Ver logs:"
echo "   sudo journalctl -u novaporra -f"
echo "   tail -f $APP_DIR/logs/novaporra.log"
echo ""
echo "6. Comandos útiles:"
echo "   sudo systemctl status novaporra   # Ver estado"
echo "   sudo systemctl stop novaporra     # Detener"
echo "   sudo systemctl restart novaporra  # Reiniciar"
echo ""
