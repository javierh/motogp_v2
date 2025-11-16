# Guía de Despliegue en LXC

## Preparación del Contenedor LXC

### Crear contenedor LXC

```bash
# En tu servidor Proxmox/LXC host
lxc-create -n novaporra -t download -- -d ubuntu -r jammy -a amd64

# O desde Proxmox web UI: Create CT
# - OS: Ubuntu 22.04
# - CPU: 1 core
# - RAM: 1024 MB
# - Disk: 8 GB
# - Network: Bridge con IP estática
```

### Configuración de Red

Asegúrate de que el contenedor tenga:
- IP estática o DHCP reservation
- Acceso a internet
- Puertos necesarios (ninguno público para el bot)

## Métodos de Despliegue

### Método 1: Script Automático (Recomendado)

Desde este ordenador, despliega al LXC:

```bash
# Si tienes SSH configurado
./deploy_to_lxc.sh root@<IP_DEL_LXC>

# Si usas lxc commands
./deploy_to_lxc.sh novaporra-container-name
```

El script:
1. Empaqueta el proyecto
2. Copia archivos al LXC
3. Ejecuta instalación automática
4. Configura MySQL
5. Crea servicio systemd

### Método 2: Instalación Manual

1. **Copiar archivos al LXC**:

```bash
# Crear tarball
tar czf novaporra.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    src/ migrations/ scripts/ requirements.txt install_lxc.sh

# Copiar al LXC
scp novaporra.tar.gz root@<IP_LXC>:/tmp/

# Conectar al LXC
ssh root@<IP_LXC>
```

2. **Dentro del LXC**:

```bash
# Extraer archivos
mkdir -p /opt/novaporra
cd /opt/novaporra
tar xzf /tmp/novaporra.tar.gz

# Ejecutar instalación
bash install_lxc.sh
```

## Configuración Post-Instalación

### 1. Obtener Token de Telegram

```bash
# En Telegram, habla con @BotFather
/newbot
# Sigue instrucciones y guarda el token
```

### 2. Configurar Variables de Entorno

```bash
# Editar .env
nano /opt/novaporra/.env

# Configurar (mínimo):
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz...
MYSQL_PASSWORD=tu_password_seguro
```

### 3. Sincronizar Datos de MotoGP

```bash
# Como usuario novaporra
sudo -u novaporra /opt/novaporra/venv/bin/python /opt/novaporra/scripts/sync_data.py

# Verifica que se descarguen eventos y pilotos
```

### 4. Crear Datos de Prueba (Opcional)

```bash
sudo -u novaporra /opt/novaporra/venv/bin/python -m src.utils.admin_scripts create_test_data
```

### 5. Iniciar Servicio

```bash
# Iniciar
sudo systemctl start novaporra

# Verificar estado
sudo systemctl status novaporra

# Ver logs
sudo journalctl -u novaporra -f

# Habilitar inicio automático
sudo systemctl enable novaporra
```

## Administración

### Comandos Útiles

```bash
# Estado del servicio
sudo systemctl status novaporra

# Reiniciar
sudo systemctl restart novaporra

# Detener
sudo systemctl stop novaporra

# Ver logs en tiempo real
sudo journalctl -u novaporra -f

# Ver logs de aplicación
tail -f /opt/novaporra/logs/novaporra.log

# Acceder a MySQL
mysql -u novaporra_user -p novaporra
```

### Actualizar el Bot

```bash
# Detener servicio
sudo systemctl stop novaporra

# Actualizar código
cd /opt/novaporra
# Copia nuevos archivos o git pull

# Actualizar dependencias si cambió requirements.txt
sudo -u novaporra /opt/novaporra/venv/bin/pip install -r requirements.txt

# Actualizar base de datos si hay cambios
mysql -u root -p novaporra < migrations/update_xxx.sql

# Reiniciar
sudo systemctl start novaporra
```

### Sincronizar Datos Manualmente

```bash
# Sincronizar calendario y pilotos
sudo -u novaporra /opt/novaporra/venv/bin/python /opt/novaporra/scripts/sync_data.py

# Sincronizar temporada específica
sudo -u novaporra /opt/novaporra/venv/bin/python /opt/novaporra/scripts/sync_data.py 2025
```

### Backup

```bash
# Backup de base de datos
mysqldump -u root -p novaporra > /backup/novaporra_$(date +%Y%m%d).sql

# Backup completo (con .env)
tar czf /backup/novaporra_full_$(date +%Y%m%d).tar.gz /opt/novaporra

# Script de backup automático (cron)
# Añadir a /etc/cron.daily/novaporra-backup:
#!/bin/bash
mysqldump -u root -pPASSWORD novaporra | gzip > /backup/novaporra_$(date +\%Y\%m\%d).sql.gz
find /backup -name "novaporra_*.sql.gz" -mtime +7 -delete
```

## Monitorización

### Recursos del Sistema

```bash
# CPU y memoria
htop

# Espacio en disco
df -h

# Logs de MySQL
tail -f /var/log/mysql/error.log
```

### Monitorizar el Bot

```bash
# Ver si el proceso está corriendo
ps aux | grep python

# Ver conexiones de red
netstat -tulpn | grep python

# Logs del bot
tail -f /opt/novaporra/logs/novaporra.log
```

## Troubleshooting

### Bot no arranca

```bash
# Ver error específico
sudo journalctl -u novaporra -n 50

# Verificar que MySQL está corriendo
sudo systemctl status mysql

# Probar conexión a base de datos
mysql -u novaporra_user -p novaporra -e "SELECT 1;"

# Verificar variables de entorno
sudo -u novaporra cat /opt/novaporra/.env
```

### No se sincronizan datos de MotoGP

```bash
# Verificar conectividad
curl -I https://api.motogp.pulselive.com/motogp/v1/results/seasons

# Ejecutar sync manualmente y ver errores
sudo -u novaporra /opt/novaporra/venv/bin/python /opt/novaporra/scripts/sync_data.py

# Ver logs
tail -f /opt/novaporra/logs/novaporra.log
```

### Bot no responde en Telegram

```bash
# Verificar token
# En el bot, usar /getMe debe responder

# Verificar que el servicio está corriendo
sudo systemctl status novaporra

# Ver logs en tiempo real
sudo journalctl -u novaporra -f
```

### Error de base de datos

```bash
# Acceder a MySQL
mysql -u root -p

# Verificar tablas
USE novaporra;
SHOW TABLES;

# Verificar usuarios
SELECT user, host FROM mysql.user WHERE user='novaporra_user';

# Re-inicializar si es necesario (¡CUIDADO! Borra datos)
mysql -u root -p novaporra < /opt/novaporra/migrations/init.sql
```

## Seguridad

### Recomendaciones

1. **Firewall**: Solo abre puertos necesarios (ninguno para el bot)
2. **SSH**: Usa claves SSH en lugar de contraseñas
3. **MySQL**: Solo escucha en localhost
4. **Backups**: Configura backups automáticos
5. **Updates**: Mantén el sistema actualizado

```bash
# Firewall básico
ufw enable
ufw allow ssh
# No necesitas abrir puertos para el bot (solo salida)

# Actualizar sistema
apt update && apt upgrade -y
```

## Rendimiento

### Recursos Estimados

- **CPU**: 0.1-0.5 core (idle) | 1 core (picos)
- **RAM**: 200-400 MB (depende de usuarios)
- **Disco**: 500 MB + logs
- **Red**: Mínima (solo API requests y Telegram)

### Optimización

```bash
# Si hay muchos usuarios, aumentar workers
# Editar /etc/systemd/system/novaporra.service
# Añadir variables de entorno si es necesario

# Limpiar logs viejos
find /opt/novaporra/logs -name "*.log.*" -mtime +30 -delete
```

## Migración desde Docker

Si decides migrar desde Docker a instalación nativa:

```bash
# Exportar datos de MySQL en Docker
docker-compose exec mysql mysqldump -u root -p novaporra > backup.sql

# Importar en MySQL nativo
mysql -u root -p novaporra < backup.sql

# Copiar .env y ajustar rutas
```
