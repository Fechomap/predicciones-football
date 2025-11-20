# Auditoría de Arquitectura y Uso de Datos

---

## ✅ ACTUALIZACIÓN 19/Nov/2025 - FASE 5 COMPLETADA

**Estado del Sistema**: ✅ **PRODUCTION-READY**

### Completado:
- ✅ PDF Profesional (12/12 secciones) según especificación final
- ✅ FootyStats Integration (64 equipos, 5 ligas al 100%)
- ✅ Auditoría Matemática aprobada (todos los cálculos correctos)
- ✅ Emojis optimizados para ReportLab
- ✅ Homologación 100% con Telegram

### Próxima Fase:
📄 Ver **`PLAN_EXPANSION_ESTRATEGICA.md`** para roadmap de:
- Nuevos mercados (BTTS, Over/Under, Player Props)
- Multi-deporte (NBA, NFL, Hockey)
- Live betting
- Machine Learning v2

---

## 1. Resumen Ejecutivo (Documento Original)

La investigación revela que el sistema actual, aunque funcional, opera como un **Producto Mínimo Viable (MVP)** enfocado casi exclusivamente en el mercado de apuestas **1X2 (Ganador del Partido)**. Esta decisión de diseño, si bien es efectiva para validar el concepto central y gestionar costos, deja sin explotar una cantidad significativa de datos valiosos disponibles a través de las APIs de `API-Football` y `FootyStats`.

La arquitectura es sólida pero minimalista. El principal cuello de botella no es técnico, sino estratégico: el sistema fue construido para hacer una cosa bien, y aún no se ha expandido para incorporar mayor complejidad o variedad de análisis. Las oportunidades más grandes y de implementación más directa radican en la expansión a nuevos mercados de apuestas (BTTS, Over/Under) y en el enriquecimiento del modelo de predicción con estadísticas granulares que ya se están recopilando pero no se utilizan en la lógica de decisión final.

## 2. Flujo de Datos Actual

El proceso de análisis de un partido sigue estos pasos:

1.  **Orquestación (`bot_service.py`):** El servicio principal `analyze_fixture` inicia el proceso.
2.  **Obtención de Datos Base (`API-Football`):** Se obtienen las estadísticas de la temporada para ambos equipos (goles a favor/en contra, partidos jugados) y las cuotas para el mercado `Match Winner`.
3.  **Análisis Principal (`poisson_analyzer.py`):** Se utiliza un modelo de Poisson simple para calcular las probabilidades de 1X2 basándose únicamente en los promedios de goles.
4.  **Obtención de Datos de Enriquecimiento (`FootyStats`):** Se obtienen estadísticas detalladas del partido y de la temporada, como porcentajes de BTTS, Over/Under, promedio de córners, tiros, etc.
5.  **Análisis de Calidad (`enhanced_analyzer.py`):** Estos datos detallados se procesan para generar un `quality_score` y una probabilidad de `BTTS`. **Críticamente, la mayoría de las estadísticas granulares (córners, tiros) no influyen en el resultado final.**
6.  **Detección de Valor (`value_detector.py`):** Se comparan las probabilidades calculadas por el modelo de Poisson con las cuotas del mercado para identificar apuestas de valor.
7.  **Persistencia (`models.py`):** Solo se guardan de forma estructurada las estadísticas agregadas de la temporada (`TeamStatistics`). El resultado completo del análisis se guarda como un objeto JSON en `AnalysisHistory`, pero los datos ricos de las APIs no se almacenan de forma estructurada para análisis futuros.

## 3. Gaps de Datos y Oportunidades Clave

A continuación se detallan las áreas donde el sistema está infrautilizando los datos disponibles.

### 3.1. Mercados de Apuestas Ignorados

-   **Oportunidad:** El sistema se centra únicamente en el mercado `Match Winner` (1X2). Las APIs, sin embargo, proveen cuotas para una amplia gama de mercados.
-   **Impacto:** Se está perdiendo la oportunidad de encontrar valor en mercados muy populares como:
    -   **Over/Under Goals (Más/Menos Goles):** Especialmente O/U 2.5.
    -   **Both Teams to Score (Ambos Equipos Anotan - BTTS).**
-   **Observación Crítica:** El `enhanced_analyzer` **ya calcula la probabilidad de BTTS** (`btts_percentage`), pero este dato solo se usa para el `quality_score` y no para detectar valor en el mercado de BTTS directamente. Esta es la oportunidad de expansión más inmediata y de menor esfuerzo.

### 3.2. Estadísticas Granulares Subutilizadas

-   **Oportunidad:** El `footystats_client` y el `enhanced_analyzer` calculan métricas detalladas como `avg_corners`, `avg_shots_on_target`, y `avg_possession`.
-   **Impacto:** Estos datos son procesados pero **no se utilizan en ningún modelo de predicción ni en la lógica de detección de valor**. Actualmente, solo contribuyen de forma indirecta y abstracta al `quality_score`.
-   **Potencial:** Estos datos podrían alimentar un modelo de Machine Learning mucho más sofisticado para predecir resultados de partidos, o para abrir mercados de apuestas completamente nuevos (ej. apuestas de córners, tarjetas).

### 3.3. Endpoints de API No Utilizados

-   **Oportunidad:** `API-Football` ofrece endpoints que no se están consumiendo.
-   **`get_fixture_statistics`:** Proporciona estadísticas detalladas de un partido específico, incluyendo **alineaciones confirmadas**, formaciones, y estadísticas de eventos en vivo. El bot actualmente opera sin saber las alineaciones, un factor crucial en cualquier análisis de partido serio.
-   **`get_team_statistics`:** Se usa de forma muy superficial. Solo se extrae el string de `form` y los goles/partidos. Se ignora información valiosa como porterías a cero (`clean_sheet`), estadísticas de penaltis, y detalles de tarjetas por período de partido.
-   **Impacto:** Ignorar las alineaciones es una debilidad significativa. El resto de los datos podrían mejorar drásticamente la precisión de cualquier modelo predictivo.

## 4. Causas Probables de la Implementación Actual

-   **Enfoque MVP:** La estrategia parece haber sido lanzar rápidamente con un caso de uso simple y claro (valor en 1X2) para probar la viabilidad del proyecto.
-   **Gestión de Costos de API:** Cada llamada a un endpoint adicional (especialmente a endpoints ricos en datos como `get_fixture_statistics`) incrementa los costos y el consumo de la cuota de peticiones por minuto/día. La arquitectura actual es económica.
-   **Complejidad de Modelado:** Implementar y validar modelos predictivos para nuevos mercados o que utilicen docenas de variables es una tarea compleja y que consume tiempo. Se optó por un modelo de Poisson por su simplicidad e interpretabilidad.

## 5. Plan de Acción Recomendado

Para evolucionar el bot y capitalizar las oportunidades identificadas, se recomienda el siguiente plan de acción incremental:

### Fase 1: Capitalizar "Low-Hanging Fruit"

1.  **Implementar Detección de Valor para BTTS:**
    -   Modificar `bot_service` para obtener las cuotas del mercado "Both Teams to Score".
    -   Crear un nuevo detector de valor (o extender el actual) que compare la `btts_percentage` calculada por `enhanced_analyzer` con las cuotas del mercado.
    -   Ajustar el formato de mensaje de Telegram para notificar sobre apuestas de valor en BTTS.

2.  **Implementar Detección de Valor para Over/Under 2.5:**
    -   Añadir lógica en `enhanced_analyzer` para calcular la probabilidad de Over/Under 2.5 (los datos de FootyStats ya lo facilitan).
    -   Obtener las cuotas del mercado "Over/Under".
    -   Implementar la lógica de detección de valor y la notificación correspondiente.

### Fase 2: Enriquecer el Modelo Predictivo

3.  **Integrar Estadísticas Clave en el Modelo Actual:**
    -   Como paso intermedio, modificar el `value_detector` para que el `quality_score` del `enhanced_analyzer` pondere el "valor" encontrado. Una apuesta de valor con un `quality_score` bajo podría ser descartada, mejorando la calidad de las alertas.

4.  **Desarrollar un Modelo Predictivo Avanzado (v2):**
    -   Crear un nuevo analizador (ej. `ml_analyzer.py`) que utilice un modelo de regresión logística o un gradient boosting (ej. XGBoost, LightGBM).
    -   **Features de entrada:** Usar las estadísticas granulares actualmente ignoradas (córners, tiros, posesión, etc.).
    -   **Objetivo:** Predecir probabilidades para 1X2, BTTS, y O/U 2.5 con mayor precisión que el modelo de Poisson.
    -   **Almacenamiento:** Modificar los `models.py` para almacenar estas estadísticas granulares de forma estructurada, permitiendo el re-entrenamiento y análisis offline del modelo.

### Fase 3: Incorporar Datos Críticos (Pre-Partido)

5.  **Evaluar la Integración de Alineaciones:**
    -   Realizar un análisis costo-beneficio de llamar al endpoint `get_fixture_statistics` de `API-Football` para obtener las alineaciones ~1 hora antes del partido.
    -   **Lógica sugerida:** El bot podría realizar un análisis preliminar días antes y, si encuentra valor potencial, ponerlo en un estado "pendiente". Una hora antes del partido, verificaría las alineaciones. Si los jugadores clave están presentes, se confirma y envía la alerta. Si no, se cancela. Esto optimizaría los costos de API.
