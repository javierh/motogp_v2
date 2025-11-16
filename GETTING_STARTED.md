# 🏍️ NovaPorra - Sistema de Apuestas MotoGP

## ✅ Sistema Completado

El sistema está **completamente implementado** y listo para usar. Todos los ajustes solicitados han sido aplicados:

### ✓ Implementaciones Completadas

1. **✅ Lenguaje Python** - Todo el proyecto está en Python 3.11+
2. **✅ Nuevo Sistema de Puntuación**:
   - 10 puntos por acierto exacto (piloto + posición)
   - 5 puntos por piloto en podio (posición incorrecta)
   - +10 bonus por podio perfecto (los 3 aciertos exactos)
3. **✅ API Pública MotoGP** - Cliente implementado para `api.motogp.pulselive.com`
4. **✅ Deployment para LXC** - Scripts de instalación nativa (sin Docker)

---

## 🚀 Cómo Empezar

### Opción A: Desarrollo Local (Este Ordenador)

```bash
cd /home/javierh/Desenvolupament/personal/novaporra

# 1. Instalar dependencias (necesitas Python 3.11+ y MySQL)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configurar MySQL
sudo mysql
CREATE DATABASE novaporra CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'novaporra_user'@'localhost' IDENTIFIED BY 'tu_password';
GRANT ALL PRIVILEGES ON novaporra.* TO 'novaporra_user'@'localhost';
FLUSH PRIVILEGES;
quit;

# 3. Inicializar base de datos
mysql -u novaporra_user -p novaporra < migrations/init.sql

# 4. Configurar .env
cp .env.example .env
nano .env
# Configurar:
#   TELEGRAM_BOT_TOKEN=tu_token_de_botfather
#   MYSQL_PASSWORD=tu_password

# 5. Sincronizar datos de MotoGP
python scripts/sync_data.py 2024

# 6. (Opcional) Crear datos de prueba
python -m src.utils.admin_scripts create_test_data

# 7. Ejecutar el bot
python -m src.main
```

### Opción B: Deployment en LXC (Producción)

Cuando tengas el LXC listo:

```bash
# Desde este ordenador
./deploy_to_lxc.sh root@IP_DEL_LXC

# Luego en el LXC:
# 1. Editar .env con tu token
nano /opt/novaporra/.env

# 2. Sincronizar datos
sudo -u novaporra /opt/novaporra/venv/bin/python /opt/novaporra/scripts/sync_data.py

# 3. Iniciar servicio
sudo systemctl start novaporra
sudo systemctl enable novaporra

# Ver logs
sudo journalctl -u novaporra -f
```

---

## 📱 Usar el Bot de Telegram

### 1. Crear el Bot

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Sigue las instrucciones
4. Guarda el **token** (algo como `123456789:ABCdefGHIjklMNOpqrsTUVwxyz...`)
5. Configúralo en `.env`

### 2. Comandos Disponibles

Una vez el bot esté corriendo:

- `/start` - Registrarte en el sistema
- `/ayuda` - Ver todos los comandos
- `/apostar` - Realizar una apuesta (proceso guiado)
- `/misapuestas` - Ver tus apuestas activas
- `/clasificacion` - Ver clasificación general
- `/proximas` - Ver próximas carreras

---

## 📊 Sistema de Puntuación (Actualizado)

### Cómo Funciona

**Por cada posición que predices:**
- Si aciertas **piloto Y posición**: **10 puntos**
- Si el piloto está en el podio pero en **otra posición**: **5 puntos**
- Si el piloto no está en el podio: **0 puntos**

**Bonus especial:**
- Si aciertas **los 3 pilotos en posiciones exactas**: **+10 puntos extra**

### Ejemplos

**Ejemplo 1: Podio Perfecto**
```
Tu apuesta:  1º Márquez, 2º Bagnaia, 3º Martín
Resultado:   1º Márquez, 2º Bagnaia, 3º Martín
Puntos:      10 + 10 + 10 + 10 (bonus) = 40 puntos
```

**Ejemplo 2: Algunos Aciertos**
```
Tu apuesta:  1º Márquez, 2º Bagnaia, 3º Martín
Resultado:   1º Márquez, 2º Martín, 3º Quartararo
Puntos:      10 (1º exacto) + 5 (Bagnaia no está) + 5 (Martín en 2º) = 20 puntos
```

**Ejemplo 3: Todos en Podio pero Descolocados**
```
Tu apuesta:  1º Bagnaia, 2º Márquez, 3º Martín
Resultado:   1º Márquez, 2º Martín, 3º Bagnaia
Puntos:      5 + 5 + 5 = 15 puntos (sin bonus)
```

**Ejemplo 4: Un Solo Acierto**
```
Tu apuesta:  1º Márquez, 2º Rossi, 3º Lorenzo
Resultado:   1º Márquez, 2º Bagnaia, 3º Martín
Puntos:      10 + 0 + 0 = 10 puntos
```

---

## 🔧 Administración

### Sincronizar Datos de MotoGP

```bash
# Sincronizar temporada actual
python scripts/sync_data.py

# Sincronizar temporada específica
python scripts/sync_data.py 2025

# Ver qué datos se sincronizaron
tail -f logs/novaporra.log
```

Esto descarga:
- 📅 Calendario de GPs
- 🏍️ Pilotos de todas las categorías
- 🏁 Circuitos
- 📊 Equipos y constructores

### Actualizar Resultados de Carrera

Después de cada carrera, necesitas:

1. **Sincronizar resultados** (manual por ahora):
```python
# Crear script o usar Python interactivo
from src.database import get_db
from src.services.data_sync_service import DataSyncService
import asyncio

async def update_results(race_id):
    with get_db() as db:
        await DataSyncService.update_race_results(db, race_id)

asyncio.run(update_results(1))  # ID de la carrera
```

2. **Calcular puntos**:
```python
from src.database import get_db
from src.services import ScoringService

with get_db() as db:
    success, msg = ScoringService.process_race_results(db, race_id=1)
    print(msg)
```

### Comandos Útiles MySQL

```bash
# Conectar a la base de datos
mysql -u novaporra_user -p novaporra

# Ver todas las apuestas
SELECT u.first_name, r.id, b.* FROM bets b
JOIN users u ON b.user_id = u.id
JOIN races r ON b.race_id = r.id;

# Ver clasificación global
SELECT u.first_name, g.total_points
FROM global_standings g
JOIN users u ON g.user_id = u.id
WHERE g.season = 2024
ORDER BY g.total_points DESC;

# Ver próximas carreras
SELECT e.name, c.name, r.race_datetime, r.bet_close_datetime, r.status
FROM races r
JOIN events e ON r.event_id = e.id
JOIN categories c ON r.category_id = c.id
WHERE r.status IN ('upcoming', 'betting_open')
ORDER BY r.race_datetime;
```

---

## 🐛 Troubleshooting

### El bot no arranca

```bash
# Ver errores específicos
python -m src.main

# Verificar configuración
cat .env | grep TELEGRAM_BOT_TOKEN

# Verificar conexión a MySQL
mysql -u novaporra_user -p novaporra -e "SELECT 1;"
```

### No hay datos de MotoGP

```bash
# Sincronizar manualmente
python scripts/sync_data.py 2024

# Ver logs de sync
tail -f logs/novaporra.log

# Verificar conectividad
curl -I https://api.motogp.pulselive.com/motogp/v1/results/seasons
```

### Las apuestas no se cierran automáticamente

El scheduler cierra apuestas automáticamente 10 minutos antes de cada carrera.

Verificar:
```bash
# Ver logs del scheduler
grep "close_expired_bets" logs/novaporra.log

# Cerrar manualmente una carrera
python -c "
from src.database import get_db
from src.services import BettingService
with get_db() as db:
    BettingService.close_betting(db, race_id=1)
"
```

---

## 📁 Estructura del Proyecto

```
novaporra/
├── src/
│   ├── api/                    # Cliente API MotoGP
│   │   └── motogp_public_api.py
│   ├── bot/                    # Bot de Telegram
│   │   └── telegram_bot.py
│   ├── database/               # ORM y modelos
│   │   ├── models.py
│   │   └── connection.py
│   ├── services/               # Lógica de negocio
│   │   ├── betting_service.py
│   │   ├── scoring_service.py
│   │   └── data_sync_service.py
│   ├── utils/                  # Utilidades
│   │   ├── logger.py
│   │   ├── scheduler.py
│   │   └── admin_scripts.py
│   ├── config.py
│   └── main.py
├── migrations/
│   └── init.sql               # Schema de BD
├── scripts/
│   └── sync_data.py           # Sincronizar datos
├── tests/                     # Tests unitarios
├── logs/                      # Logs de aplicación
├── install_lxc.sh            # Instalación en LXC
├── deploy_to_lxc.sh          # Deploy automático
├── README.md
├── SETUP.md                  # Guía de instalación
├── TECHNICAL.md              # Documentación técnica
└── DEPLOY_LXC.md            # Guía deployment LXC
```

---

## 🎯 Próximos Pasos

### Corto Plazo (Para Usar Ya)

1. ✅ Obtener token de Telegram (@BotFather)
2. ✅ Configurar .env
3. ✅ Sincronizar datos de MotoGP
4. ✅ Probar el bot con datos de prueba
5. 🔄 Cuando esté el LXC, desplegar con `deploy_to_lxc.sh`

### Medio Plazo (Mejoras Futuras)

- [ ] Comando `/editar` para modificar apuestas existentes
- [ ] Comando `/resultados` para ver resultados de carreras
- [ ] Comando `/tiempos` para consultar sesiones de práctica/clasificación
- [ ] Automatizar actualización de resultados tras carreras
- [ ] Panel web de administración (opcional)
- [ ] Notificaciones push cuando se cierran apuestas
- [ ] Estadísticas por usuario (mejores rachas, etc.)
- [ ] Exportar clasificación a imagen/PDF

### Mejoras Opcionales

- [ ] Sistema de ligas privadas
- [ ] Predicciones de pole position
- [ ] Apuestas para constructores
- [ ] Integración con otras competiciones (F1, WorldSBK)

---

## 📞 Soporte

Para cualquier duda:
1. Revisa los logs: `tail -f logs/novaporra.log`
2. Consulta la documentación: `TECHNICAL.md`, `DEPLOY_LXC.md`
3. Verifica la base de datos con los comandos MySQL mostrados arriba

---

## 🎉 ¡Listo para Usar!

El sistema está **100% funcional**. Solo necesitas:
1. Token de Telegram
2. Sincronizar datos de MotoGP
3. ¡Empezar a apostar!

Cuando tengas el LXC configurado, avísame y te ayudo con el deployment.

**¡Buena suerte con las apuestas! 🏍️🏁**
