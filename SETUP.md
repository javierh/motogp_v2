# Guía de Instalación y Configuración

## Requisitos Previos

- Docker y Docker Compose instalados
- Token de bot de Telegram
- (Opcional) Acceso a API de MotoGP.com

## Pasos de Instalación

### 1. Obtener Token de Telegram

1. Abre Telegram y busca `@BotFather`
2. Envía el comando `/newbot`
3. Sigue las instrucciones para crear tu bot
4. Guarda el token que te proporciona

### 2. Configurar Variables de Entorno

```bash
cp .env.example .env
nano .env  # o usa tu editor favorito
```

Configura al menos estas variables:
```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
MYSQL_PASSWORD=contraseña_segura
MYSQL_ROOT_PASSWORD=contraseña_root_segura
```

### 3. Iniciar Servicios con Docker

```bash
# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f bot
```

### 4. Crear Datos de Prueba (Opcional)

```bash
# Acceder al contenedor
docker-compose exec bot bash

# Crear datos de prueba
python -m src.utils.admin_scripts create_test_data
```

### 5. Verificar Funcionamiento

1. Busca tu bot en Telegram por su username
2. Envía `/start` para registrarte
3. Usa `/ayuda` para ver comandos disponibles
4. Prueba `/apostar` para crear una apuesta

## Configuración de la API de MotoGP

### Opción 1: API Oficial (Recomendado)

Si tienes acceso a la API oficial de MotoGP:

```env
MOTOGP_API_URL=https://api.motogp.com/
MOTOGP_API_KEY=tu_api_key
MOTOGP_API_SECRET=tu_api_secret
```

### Opción 2: Entrada Manual de Datos

Sin API, necesitarás:
1. Crear circuitos manualmente en la BD
2. Crear eventos para cada GP
3. Añadir pilotos y sus equipos
4. Crear las carreras para cada evento

Script de ayuda:
```python
python -m src.utils.admin_scripts create_test_data
```

### Opción 3: Web Scraping (Limitado)

El cliente incluye funciones básicas de scraping como fallback, pero requiere desarrollo adicional.

## Mantenimiento

### Backup de la Base de Datos

```bash
# Crear backup
docker-compose exec mysql mysqldump -u root -p novaporra > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker-compose exec -T mysql mysql -u root -p novaporra < backup_20241116.sql
```

### Ver Logs

```bash
# Logs del bot
docker-compose logs -f bot

# Logs de MySQL
docker-compose logs -f mysql

# Logs locales
tail -f logs/novaporra.log
```

### Actualizar el Sistema

```bash
# Detener servicios
docker-compose down

# Actualizar código (git pull, etc.)
git pull origin main

# Reconstruir y reiniciar
docker-compose build
docker-compose up -d
```

## Resolución de Problemas

### El bot no responde

1. Verificar que el contenedor está corriendo:
```bash
docker-compose ps
```

2. Ver logs para errores:
```bash
docker-compose logs bot
```

3. Verificar token de Telegram:
```bash
docker-compose exec bot env | grep TELEGRAM
```

### Error de conexión a base de datos

1. Verificar que MySQL está corriendo:
```bash
docker-compose ps mysql
```

2. Probar conexión:
```bash
docker-compose exec mysql mysql -u novaporra_user -p -e "SELECT 1;"
```

3. Verificar credenciales en .env

### No hay carreras disponibles

1. Crear datos de prueba:
```bash
docker-compose exec bot python -m src.utils.admin_scripts create_test_data
```

2. O añadir datos manualmente vía MySQL

## Próximos Pasos

1. **Integrar API de MotoGP**: Implementar los métodos del cliente API
2. **Automatización**: El scheduler cerrará apuestas automáticamente
3. **Actualizar resultados**: Tras cada carrera, actualizar resultados en BD
4. **Calcular puntos**: El sistema calculará automáticamente

## Soporte

Para reportar problemas o solicitar funciones:
- Crea un issue en el repositorio
- Contacta al administrador del sistema
