# Documentación Técnica - NovaPorra

## Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────┐
│  Telegram Bot   │
│   (Frontend)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│   Application   │◄────►│   Services   │
│     Layer       │      │  (Business)  │
└────────┬────────┘      └──────┬───────┘
         │                      │
         ▼                      ▼
┌─────────────────┐      ┌──────────────┐
│    Database     │      │  MotoGP API  │
│     (MySQL)     │      │    Client    │
└─────────────────┘      └──────────────┘
```

### Flujo de Datos

1. **Usuario → Telegram**: Usuario envía comando
2. **Telegram → Bot**: Bot recibe actualización
3. **Bot → Services**: Procesa lógica de negocio
4. **Services → Database**: Consulta/actualiza datos
5. **Database → Services**: Retorna resultados
6. **Services → Bot**: Prepara respuesta
7. **Bot → Telegram**: Envía mensaje al usuario

## Estructura de Directorios

```
novaporra/
├── src/
│   ├── bot/              # Bot de Telegram
│   │   ├── __init__.py
│   │   └── telegram_bot.py
│   ├── api/              # Cliente API MotoGP
│   │   ├── __init__.py
│   │   └── motogp_client.py
│   ├── database/         # ORM y modelos
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   └── models.py
│   ├── services/         # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── betting_service.py
│   │   └── scoring_service.py
│   ├── utils/            # Utilidades
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── scheduler.py
│   │   └── admin_scripts.py
│   ├── config.py         # Configuración
│   └── main.py           # Punto de entrada
├── migrations/           # SQL migrations
│   └── init.sql
├── tests/               # Tests unitarios
├── logs/                # Archivos de log
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
└── SETUP.md
```

## Modelos de Datos

### Relaciones Principales

```
Users ──── Bets ──── Races ──── Events ──── Circuits
  │          │        │
  │          │        └──── Categories
  │          │        │
  │          │        └──── RaceTypes
  │          │
  │          └──── Riders
  │
  └──── ChampionshipStandings
  └──── GlobalStandings
```

### Modelo de Datos Completo

Ver `migrations/init.sql` para el esquema completo.

## Servicios

### BettingService

Gestiona las apuestas de los usuarios:

- `create_bet()`: Crea nueva apuesta
- `update_bet()`: Actualiza apuesta existente
- `get_user_bet()`: Obtiene apuesta de usuario
- `close_betting()`: Cierra apuestas para una carrera
- `can_place_bet()`: Valida si se puede apostar

### ScoringService

Calcula puntos y actualiza clasificaciones:

- `calculate_bet_score()`: Calcula puntos de una apuesta
- `process_race_results()`: Procesa resultados de carrera
- `update_championship_standings()`: Actualiza clasificación por categoría
- `update_global_standings()`: Actualiza clasificación global
- `get_championship_standings()`: Obtiene clasificación
- `get_global_standings()`: Obtiene clasificación global

## Bot de Telegram

### Comandos Implementados

| Comando | Descripción | Estado |
|---------|-------------|--------|
| `/start` | Registro de usuario | ✅ |
| `/ayuda` | Mostrar ayuda | ✅ |
| `/apostar` | Crear apuesta (conversación) | ✅ |
| `/editar` | Editar apuesta | 🔄 |
| `/misapuestas` | Ver apuestas activas | ✅ |
| `/clasificacion` | Ver clasificación | ✅ |
| `/proximas` | Ver próximas carreras | ✅ |
| `/resultados` | Ver resultados | 🔄 |
| `/tiempos` | Ver tiempos de sesiones | 🔄 |

✅ Implementado | 🔄 Pendiente

### Flujo de Conversación para Apuestas

```
/apostar
  ↓
Seleccionar Categoría (MotoGP/Moto2/Moto3)
  ↓
Seleccionar Tipo de Carrera (Sprint/Race)
  ↓
Seleccionar 1er Piloto
  ↓
Seleccionar 2º Piloto
  ↓
Seleccionar 3er Piloto
  ↓
Confirmar Apuesta
  ↓
Apuesta Guardada
```

## Sistema de Puntos

### Puntuación por Posición

**Carrera Principal:**
- 1ª posición: 25 puntos
- 2ª posición: 20 puntos
- 3ª posición: 16 puntos

**Sprint Race:**
- 1ª posición: 12 puntos
- 2ª posición: 9 puntos
- 3ª posición: 7 puntos

### Clasificaciones

1. **Por Categoría**: Puntos solo de esa categoría (MotoGP, Moto2, Moto3)
2. **Global**: Suma de puntos de todas las categorías

## Scheduler (Tareas Automáticas)

### Tareas Programadas

| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `close_expired_bets` | 1 minuto | Cierra apuestas cuando expira el tiempo |
| `send_closing_warnings` | 5 minutos | Avisa 15 min antes del cierre |
| `update_race_data` | 1 hora | Actualiza datos desde API |

## API de MotoGP

### Cliente Implementado

El cliente `MotoGPAPIClient` proporciona métodos para:

- `get_current_season()`: Temporada actual
- `get_calendar()`: Calendario de carreras
- `get_riders()`: Lista de pilotos
- `get_session_results()`: Resultados de sesiones
- `get_race_results()`: Resultados de carreras
- `get_championship_standings()`: Clasificación oficial

**Nota**: Requiere implementación específica según API disponible.

## Notificaciones

### Tipos de Notificaciones

1. **Cierre de Apuestas Inminente** (15 min antes)
   - Se envía a usuarios con apuestas
   - Permite editar antes del cierre

2. **Apuestas Cerradas**
   - Se envía cuando se cierra el plazo
   - Muestra resumen de todas las apuestas

3. **Resultados de Carrera**
   - Se envía tras procesar resultados
   - Muestra puntos obtenidos

4. **Actualización de Clasificación**
   - Se envía tras actualizar standings
   - Muestra posición actual

## Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/

# Con cobertura
pytest --cov=src tests/

# Test específico
pytest tests/test_betting_service.py
```

### Crear Datos de Prueba

```bash
python -m src.utils.admin_scripts create_test_data
```

## API REST (Futuro)

Potencial extensión para crear API REST:

```
GET  /api/events          # Listar eventos
GET  /api/races           # Listar carreras
POST /api/bets            # Crear apuesta
GET  /api/standings       # Clasificación
```

## Mejoras Futuras

### Prioridad Alta
- [ ] Implementar integración real con API MotoGP
- [ ] Comando `/editar` para modificar apuestas
- [ ] Mostrar resultados de carreras
- [ ] Consultar tiempos de sesiones

### Prioridad Media
- [ ] Sistema de bonificaciones (ej: bonus por podio completo)
- [ ] Estadísticas por usuario
- [ ] Gráficos de evolución
- [ ] Exportar datos a CSV/PDF

### Prioridad Baja
- [ ] Panel web de administración
- [ ] API REST pública
- [ ] Integración con otros deportes
- [ ] Sistema de ligas privadas

## Seguridad

### Consideraciones

1. **Tokens**: Nunca commitear .env al repositorio
2. **Passwords**: Usar contraseñas fuertes para MySQL
3. **API Keys**: Proteger claves de API en variables de entorno
4. **Validación**: Validar siempre input de usuarios
5. **SQL Injection**: Usar ORM (SQLAlchemy) previene esto

### Backups

```bash
# Backup automático diario (cron)
0 2 * * * cd /path/to/novaporra && docker-compose exec mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD novaporra > backups/backup_$(date +\%Y\%m\%d).sql
```

## Contribución

### Estilo de Código

- Seguir PEP 8
- Docstrings en formato Google
- Type hints en funciones públicas
- Tests para nueva funcionalidad

### Commit Messages

```
<tipo>: <descripción>

[cuerpo opcional]

Tipos: feat, fix, docs, style, refactor, test, chore
```

## Licencia

MIT License - Ver LICENSE file
