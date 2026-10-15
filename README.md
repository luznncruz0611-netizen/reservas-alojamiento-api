# 🏨 Sistema de Reservas de Alojamiento — API REST

API REST desarrollada con **FastAPI** y **MongoDB** (una sola colección: `reservas`) para administrar reservas de un establecimiento de alojamiento.

- **Producción (Vercel):** `https://<tu-proyecto>.vercel.app`
- **Documentación interactiva (Swagger):** `https://<tu-proyecto>.vercel.app/docs`
- **Documentación alternativa (ReDoc):** `https://<tu-proyecto>.vercel.app/redoc`

## Estructura

```
├── .github/workflows/ci.yml   # GitHub Actions (lint + tests)
├── api/v1/reservas.py         # Endpoints
├── core/                      # Configuración (.env) y conexión a MongoDB
├── schemas/reserva.py         # Modelos y validaciones (Pydantic)
├── utils/helpers.py           # ObjectId, serialización, cruce de fechas
├── tests/                     # Pruebas con pytest + mongomock
├── main.py                    # Aplicación FastAPI
├── requirements.txt
└── .env.example
```

## Documento de la colección `reservas`

```json
{
  "_id": "665f1c2e8a1b2c3d4e5f6a7b",
  "huesped": "Juan Pérez",
  "email": "juan@correo.com",
  "telefono": "+591 70012345",
  "habitacion": "101",
  "fecha_entrada": "2026-11-10",
  "fecha_salida": "2026-11-15",
  "cantidad_personas": 2,
  "estado": "pendiente",
  "servicios": ["desayuno", "wifi"],
  "alojamiento": { "nombre": "Hotel Sol Andino", "ciudad": "Cochabamba" }
}
```

Estados válidos: `pendiente`, `confirmada`, `cancelada`, `completada`.

## Endpoints (prefijo `/api/v1`)

| # | Método | Ruta | Descripción |
|---|--------|------|-------------|
| 1 | POST | `/reservas/` | Registrar reserva |
| 2 | GET | `/reservas/` | Listar todas (paginación `skip`, `limit`) |
| 3 | GET | `/reservas/{id}` | Consultar por identificador |
| 4 | PUT | `/reservas/{id}` | Modificar (campos parciales) |
| 5a | PATCH | `/reservas/{id}/cancelar` | Cancelar (estado → `cancelada`) |
| 5b | DELETE | `/reservas/{id}` | Eliminar definitivamente |
| 6 | GET | `/reservas/buscar?huesped=juan` | Buscar por nombre del huésped |
| 7 | GET | `/reservas/estado/{estado}` | Filtrar por estado |
| 8 | GET | `/reservas/habitacion/{habitacion}` | Filtrar por habitación |
| 9 | GET | `/reservas/fechas?fecha_entrada=2026-11-10` | Filtrar por fecha de entrada/salida (exacta o rangos `entrada_desde`, `entrada_hasta`, `salida_desde`, `salida_hasta`) |
| 10 | GET | `/reservas/servicio/{servicio}` | Reservas que incluyen un servicio |

## Validaciones y manejo de errores

- Email válido, teléfono con formato válido, `cantidad_personas` entre 1 y 20.
- `fecha_salida` debe ser posterior a `fecha_entrada`.
- Estado restringido a los valores permitidos.
- **400** ID de MongoDB inválido · **404** reserva no encontrada · **409** habitación ya reservada en esas fechas · **422** datos inválidos · **503** base de datos no disponible.

## Ejecutar en local

```bash
git clone https://github.com/luznncruz0611-netizen/reservas-alojamiento-api.git
cd reservas-alojamiento-api 
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env            # completar MONGODB_URI
uvicorn main:app --reload
```

Abrir http://127.0.0.1:8000/docs. Tests: `pytest -v`.

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `MONGODB_URI` | Cadena de conexión de MongoDB Atlas |
| `DB_NAME` | Nombre de la base de datos (`reservas_db`) |
| `COLLECTION_NAME` | Colección única (`reservas`) |

El archivo `.env` **no se sube** al repositorio (está en `.gitignore`). En Vercel se configuran en *Settings → Environment Variables*.

## Flujo de trabajo Git

`main` (producción) ← `develop` (integración) ← `feature/*`. Cada funcionalidad se desarrolla en una rama `feature/...`, se abre un Pull Request hacia `develop` y GitHub Actions ejecuta lint y tests antes de fusionar.
