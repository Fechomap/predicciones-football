# ⚽ Football Betting Analytics Bot

Bot inteligente de análisis de apuestas deportivas con detección automática de value bets utilizando distribución de Poisson y análisis estadístico.

## 🎯 Características

- 📊 **Análisis Estadístico**: Modelo Poisson para predicciones precisas
- 💰 **Detección de Value Bets**: Identifica oportunidades con edge positivo
- 📱 **Notificaciones Telegram**: Alertas automáticas en tiempo real
- 🗄️ **Multi-entorno**: Soporte para desarrollo local y producción (Railway)
- ⚡ **Optimizado**: Cache inteligente que reduce 95% las llamadas API
- 🎲 **Gestión de Bankroll**: Kelly Criterion para stakes óptimos

## 🚀 Quick Start

### 1. Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd football-betting-bot

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

### 3. Inicializar Base de Datos

```bash
# Para desarrollo local (PostgreSQL)
python3 test_db.py
```

### 4. Ejecutar Bot

```bash
./start.sh
```

## 📚 Documentación

**Orden de lectura recomendado:**

1. 📖 **[docs/INDEX.md](docs/INDEX.md)** - Índice completo de documentación
2. 🏗️ **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitectura del sistema
3. 🚀 **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Guía de deployment
4. 🚂 **[docs/RAILWAY_CONFIG.md](docs/RAILWAY_CONFIG.md)** - Configuración Railway
5. 🔧 **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Guía de desarrollo

## 🛠️ Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `./start.sh` | Iniciar el bot |
| `./switch_env.sh dev` | Cambiar a desarrollo |
| `./switch_env.sh prod` | Cambiar a producción |
| `python3 test_db.py` | Probar conexión BD |
| `python3 migrate_to_production.py` | Migrar tablas a Railway |

## 🏗️ Estructura del Proyecto

```
football-betting-bot/
├── src/
│   ├── api/              # Cliente API-Football
│   ├── analyzers/        # Modelo Poisson y análisis
│   ├── database/         # Modelos SQLAlchemy
│   ├── notifications/    # Bot Telegram
│   ├── services/         # Lógica de negocio
│   └── utils/            # Utilidades y configuración
├── docs/                 # Documentación
├── tests/               # Tests unitarios
├── main.py              # Punto de entrada
├── .env.example         # Plantilla de configuración
└── start.sh             # Script de inicio
```

## 🌍 Entornos

### Desarrollo (Local)
- **Database**: PostgreSQL local
- **Telegram**: Bot de prueba
- **API Calls**: Optimizadas con cache

### Producción (Railway)
- **Database**: Railway PostgreSQL
- **Telegram**: Bot de producción
- **Monitoring**: Railway dashboard

## 📊 Tecnologías

- **Python 3.11+**
- **PostgreSQL** - Base de datos
- **SQLAlchemy** - ORM
- **python-telegram-bot** - Bot Telegram
- **scipy** - Distribución de Poisson
- **pydantic** - Validación de configuración
- **APScheduler** - Tareas programadas

## 🔑 Variables de Entorno Principales

```env
# Entorno
ENVIRONMENT=development  # o production

# API-Football
RAPIDAPI_KEY=your_key

# Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# Base de Datos
DATABASE_URL=postgresql://...
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es privado y confidencial.

## 👥 Equipo

Desarrollado con ❤️ por el equipo de análisis deportivo.

## 📧 Soporte

Para preguntas o soporte, consulta la documentación en `docs/` o contacta al equipo de desarrollo.
