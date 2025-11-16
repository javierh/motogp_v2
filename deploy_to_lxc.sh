#!/bin/bash
# Quick deployment script to LXC container
# Usage: ./deploy_to_lxc.sh [lxc_container_name_or_ip]

set -e

LXC_TARGET=${1:-""}

if [ -z "$LXC_TARGET" ]; then
    echo "Usage: $0 <lxc_container_name_or_ip>"
    echo "Example: $0 novaporra-lxc"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

echo "🏍️  Desplegando NovaPorra a LXC: $LXC_TARGET"
echo "============================================"
echo ""

# Create deployment tarball
echo "📦 Creando paquete de despliegue..."
TEMP_DIR=$(mktemp -d)
DEPLOY_TAR="$TEMP_DIR/novaporra-deploy.tar.gz"

tar czf "$DEPLOY_TAR" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='logs/*' \
    --exclude='.env' \
    --exclude='*.db' \
    src/ \
    migrations/ \
    scripts/ \
    requirements.txt \
    install_lxc.sh \
    README.md \
    SETUP.md \
    TECHNICAL.md

echo "✅ Paquete creado: $(du -h "$DEPLOY_TAR" | cut -f1)"

# Check if target is IP or container name
if [[ $LXC_TARGET =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # It's an IP address
    DEPLOY_METHOD="ssh"
    SSH_TARGET="root@$LXC_TARGET"
    
    echo "📤 Copiando archivos vía SSH a $SSH_TARGET..."
    scp "$DEPLOY_TAR" "$SSH_TARGET:/tmp/"
    
    echo "🔧 Ejecutando instalación remota..."
    ssh "$SSH_TARGET" <<'ENDSSH'
        cd /tmp
        mkdir -p /opt/novaporra
        tar xzf novaporra-deploy.tar.gz -C /opt/novaporra
        cd /opt/novaporra
        bash install_lxc.sh
ENDSSH
else
    # It's a container name (assuming lxc command is available)
    DEPLOY_METHOD="lxc"
    
    echo "📤 Copiando archivos al contenedor LXC..."
    lxc file push "$DEPLOY_TAR" "$LXC_TARGET/tmp/novaporra-deploy.tar.gz"
    
    echo "🔧 Ejecutando instalación en contenedor..."
    lxc exec "$LXC_TARGET" -- bash <<'ENDLXC'
        cd /tmp
        mkdir -p /opt/novaporra
        tar xzf novaporra-deploy.tar.gz -C /opt/novaporra
        cd /opt/novaporra
        bash install_lxc.sh
ENDLXC
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Despliegue completado!"
echo ""
echo "📋 Conecta al contenedor y configura:"
echo ""
if [ "$DEPLOY_METHOD" = "ssh" ]; then
    echo "   ssh $SSH_TARGET"
else
    echo "   lxc exec $LXC_TARGET -- bash"
fi
echo ""
echo "Luego ejecuta:"
echo "   nano /opt/novaporra/.env  # Configura TELEGRAM_BOT_TOKEN"
echo "   sudo systemctl start novaporra"
echo ""
