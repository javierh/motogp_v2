# NovaPorra - Sistema de Apuestas MotoGP

Sistema de apuestas entre amigos para las carreras de MotoGP, Moto2 y Moto3.

## 🏍️ Características

- **Apuestas de podio**: Los jugadores predicen el top 3 de cada categoría
- **Carreras Sprint y Principales**: Apuestas separadas para MotoGP
- **Límite de tiempo**: Edición de apuestas hasta 10 minutos antes de cada carrera
- **Integración con Telegram**: Interfaz completa vía bot de Telegram
- **Datos en tiempo real**: Actualización automática desde API de MotoGP.com
- **Sistema de puntos**: Clasificación por categoría y global
- **Notificaciones**: Alertas de cierre de apuestas y resultados

## 📊 Sistema de Puntos

### Sistema de Puntuación
- **Acierto exacto** (piloto + posición correcta): **10 puntos**
- **Piloto en podio** (posición incorrecta): **5 puntos**
- **Bonus por podio perfecto** (los 3 aciertos exactos): **+10 puntos**

### Ejemplo
Si predices: 1º Márquez, 2º Bagnaia, 3º Martín
Y el resultado es: 1º Márquez, 2º Martín, 3º Bagnaia

Puntuación:
- Márquez (1º): 10 puntos (acierto exacto)
- Bagnaia (2º): 5 puntos (está en podio pero en 3ª)
- Martín (3º): 5 puntos (está en podio pero en 2ª)
- **Total: 20 puntos**

Si aciertas los 3 en posición exacta: 10+10+10+10(bonus) = **40 puntos**

### Clasificaciones
- Clasificación por categoría (MotoGP, Moto2, Moto3)
- Clasificación global (suma de todas las categorías)

## 🛠️ Tecnologías

- **Backend**: Python 3.11+
- **Base de datos**: MySQL 8.0
- **Bot**: python-telegram-bot
- **API**: Cliente para API pública de MotoGP (api.motogp.pulselive.com)
- **Containerización**: Docker (opcional) o instalación nativa para LXC

## 📁 Estructura del Proyecto

```
novaporra/
├── src/
│   ├── bot/              # Bot de Telegram
│   ├── api/              # Cliente API MotoGP
│   ├── database/         # Modelos y gestión de BD
│   ├── services/         # Lógica de negocio
│   └── utils/            # Utilidades
├── migrations/           # Migraciones de BD
├── config/              # Configuración
├── tests/               # Tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🚀 Instalación

### Opción 1: Docker (Desarrollo/Testing)

#### Requisitos previos
- Docker y Docker Compose
- Token de bot de Telegram (obtener de @BotFather)

#### Configuración

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd novaporra
```

2. Usar script de inicio rápido:
```bash
./quickstart.sh
```

O manualmente:

```bash
cp .env.example .env
nano .env  # Configurar TELEGRAM_BOT_TOKEN
docker-compose up -d
```

### Opción 2: LXC Container (Producción)

**Recomendado para homelab**

Ver guía completa: [DEPLOY_LXC.md](DEPLOY_LXC.md)

#### Quick Start

```bash
# Desde este ordenador
./deploy_to_lxc.sh root@<IP_LXC>

# O dentro del LXC
bash install_lxc.sh
```

#### Requisitos
- Contenedor LXC con Ubuntu 22.04
- 1 CPU core, 1GB RAM, 8GB disco
- Python 3.10+
- MySQL 8.0+

## 📱 Uso del Bot de Telegram

### Comandos disponibles

- `/start` - Registrarse en el sistema
- `/apostar` - Realizar apuesta para próximo GP
- `/editar` - Modificar apuesta existente
- `/misapuestas` - Ver tus apuestas actuales
- `/clasificacion` - Ver clasificación del campeonato
- `/tiempos` - Consultar tiempos de entrenamientos
- `/resultados` - Ver resultados de última carrera
- `/ayuda` - Mostrar ayuda

## 🔧 Desarrollo

### Instalación local

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Ejecutar tests

```bash
pytest tests/
```

### Migraciones de base de datos

```bash
python manage.py migrate
```

## 📝 Licencia

MIT License

## 👥 Contribuciones

Proyecto privado para uso entre amigos.
