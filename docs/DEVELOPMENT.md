# 🔧 Guía de Desarrollo

## 🚀 Setup Inicial

### Prerrequisitos

- Python 3.11+
- PostgreSQL 14+
- Git
- Cuenta en API-Football
- Bot de Telegram

### Instalación

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd football-betting-bot

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
nano .env

# 5. Inicializar base de datos
python3 test_db.py

# 6. Ejecutar bot
./start.sh
```

## 📁 Estructura del Código

```
src/
├── api/                    # Integración API-Football
│   ├── api_football.py     # Cliente principal
│   └── rate_limiter.py     # Control de rate limiting
│
├── analyzers/              # Modelos de análisis
│   ├── poisson_analyzer.py # Distribución de Poisson
│   ├── form_analyzer.py    # Análisis de forma
│   └── value_detector.py   # Detección de value bets
│
├── database/               # Capa de persistencia
│   ├── models.py          # Modelos SQLAlchemy
│   └── connection.py      # Gestión de conexiones
│
├── notifications/          # Bot de Telegram
│   ├── telegram_bot.py    # Cliente Telegram
│   ├── telegram_commands.py
│   ├── telegram_handlers.py
│   ├── telegram_menu.py
│   └── message_formatter.py
│
├── services/              # Lógica de negocio
│   ├── bot_service.py     # Orquestador principal
│   ├── data_collector.py  # Recolección de datos
│   ├── fixtures_service.py # Gestión de fixtures
│   └── scheduler.py       # Tareas programadas
│
└── utils/                 # Utilidades
    ├── config.py          # Configuración con Pydantic
    ├── logger.py          # Setup de logging
    └── cache.py           # Cache en memoria
```

## 💻 Convenciones de Código

### Style Guide

Seguimos **PEP 8** con estas especificaciones:

```python
# Imports ordenados
import standard_library
import third_party
from src.module import something

# Type hints
def analyze_fixture(fixture_id: int) -> Dict[str, Any]:
    """
    Docstring con descripción clara
    
    Args:
        fixture_id: ID del partido
        
    Returns:
        Diccionario con análisis
    """
    pass

# Naming conventions
ClassName
function_name()
CONSTANT_NAME
_private_method()
```

### Logging

```python
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

logger.debug("Información detallada")
logger.info("Evento importante")
logger.warning("Advertencia")
logger.error("Error")
```

### Error Handling

```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Error en operación: {e}")
    # Manejo apropiado
    raise
finally:
    # Cleanup
    pass
```

## 🔧 Configuración

### Variables de Entorno

```env
# Obligatorias
RAPIDAPI_KEY=<tu-key>
TELEGRAM_BOT_TOKEN=<tu-token>
DATABASE_URL=<connection-string>

# Opcionales
LOG_LEVEL=INFO
CHECK_INTERVAL=30
MINIMUM_EDGE=0.05
```

### Pydantic Config

El sistema usa Pydantic para validación automática:

```python
from src.utils.config import Config

# Acceso a configuración
Config.RAPIDAPI_KEY
Config.MINIMUM_EDGE
Config.ENABLED_LEAGUES
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/analyzers/

# Con coverage
pytest --cov=src tests/
```

### Escribir Tests

```python
# tests/analyzers/test_poisson.py
import pytest
from src.analyzers.poisson_analyzer import PoissonAnalyzer

def test_calculate_expected_goals():
    """Test cálculo de goles esperados"""
    home_stats = {"home_matches": 10, "home_goals_scored": 15}
    away_stats = {"away_matches": 10, "away_goals_scored": 12}
    
    home_goals, away_goals = PoissonAnalyzer.calculate_expected_goals(
        home_stats, away_stats, league_id=262
    )
    
    assert home_goals > 0
    assert away_goals > 0
```

## 🐛 Debugging

### VS Code Launch Configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Bot",
      "type": "python",
      "request": "launch",
      "program": "main.py",
      "console": "integratedTerminal",
      "env": {
        "ENVIRONMENT": "development"
      }
    }
  ]
}
```

### Logs Útiles

```python
# Ver qué fixtures se están procesando
logger.info(f"Processing fixture {fixture_id}")

# Debug de predicciones
logger.debug(f"Probabilities: {probabilities}")

# Error con contexto
logger.error(f"Failed to analyze fixture {fixture_id}: {e}")
```

## 🔄 Git Workflow

### Branches

```
main/master  → Producción
develop      → Desarrollo activo
feature/*    → Nuevas features
hotfix/*     → Fixes urgentes
```

### Commits

```bash
# Formato
<tipo>: <descripción>

# Ejemplos
feat: Add support for multiple leagues
fix: Correct Poisson calculation for high scores  
docs: Update deployment guide
refactor: Optimize database queries
test: Add tests for value detector
```

### Pull Requests

1. Crear branch desde `develop`
2. Hacer commits atómicos
3. Escribir tests
4. Actualizar documentación
5. Abrir PR con descripción clara

## 🎯 Tareas Comunes

### Agregar Nueva Liga

```python
# 1. Agregar en config.py
LEAGUE_CONFIG = {
    999: {  # ID de la liga
        "name": "Nueva Liga",
        "country": "País",
        "priority": 3,
        "emoji": "🏆"
    }
}

# 2. Agregar al .env
ENABLED_LEAGUES=262,39,999
```

### Modificar Modelo de Predicción

```python
# src/analyzers/poisson_analyzer.py

def calculate_expected_goals(
    home_stats: Dict,
    away_stats: Dict,
    league_id: int = None
) -> Tuple[float, float]:
    """
    Tu lógica aquí
    """
    # ...
    return home_goals, away_goals
```

### Agregar Comando de Telegram

```python
# src/notifications/telegram_commands.py

async def nuevo_comando(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Descripción del comando"""
    await update.message.reply_text("Respuesta")
```

## 📦 Dependencias

### Principales

```
python-telegram-bot  # Bot de Telegram
sqlalchemy          # ORM
psycopg2-binary    # PostgreSQL driver
scipy              # Distribución de Poisson
pydantic           # Validación
APScheduler        # Tareas programadas
```

### Actualizar

```bash
# Ver dependencias desactualizadas
pip list --outdated

# Actualizar
pip install --upgrade package-name

# Actualizar requirements.txt
pip freeze > requirements.txt
```

## 🚧 Troubleshooting Común

### Error de Conexión BD

```bash
# Verificar PostgreSQL está corriendo
pg_isready

# Probar conexión
python3 test_db.py
```

### Rate Limit Excedido

```python
# Verificar configuración
from src.api.rate_limiter import RateLimiter
# Max: 250 req/min
```

### Telegram Bot No Responde

```bash
# Verificar token
python3 -c "from src.utils.config import Config; print(Config.TELEGRAM_BOT_TOKEN)"

# Verificar conexión
curl https://api.telegram.org/bot<TOKEN>/getMe
```

## 📚 Recursos

- [Documentación API-Football](https://www.api-football.com/documentation-v3)
- [python-telegram-bot Docs](https://docs.python-telegram-bot.org/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Poisson Distribution](https://en.wikipedia.org/wiki/Poisson_distribution)
