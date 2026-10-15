import mongomock
import pytest
from fastapi.testclient import TestClient

from core.database import get_collection
from main import app

COL = mongomock.MongoClient().db.reservas


@pytest.fixture(autouse=True)
def limpiar():
    COL.delete_many({})
    app.dependency_overrides[get_collection] = lambda: COL
    yield
    app.dependency_overrides.clear()


client = TestClient(app)

BASE = {
    "huesped": "Juan Pérez",
    "email": "juan@correo.com",
    "telefono": "+591 70012345",
    "habitacion": "101",
    "fecha_entrada": "2026-11-10",
    "fecha_salida": "2026-11-15",
    "cantidad_personas": 2,
    "servicios": ["desayuno", "wifi"],
    "alojamiento": {"nombre": "Hotel Sol Andino", "ciudad": "Cochabamba"},
}


def crear(**kw):
    return client.post("/api/v1/reservas/", json={**BASE, **kw})


def test_crear_y_obtener():
    r = crear()
    assert r.status_code == 201
    rid = r.json()["_id"]
    assert r.json()["estado"] == "pendiente"
    assert client.get(f"/api/v1/reservas/{rid}").json()["huesped"] == "Juan Pérez"


def test_fechas_invalidas():
    assert crear(fecha_salida="2026-11-01").status_code == 422


def test_email_invalido():
    assert crear(email="no-es-email").status_code == 422


def test_id_invalido_y_no_encontrado():
    assert client.get("/api/v1/reservas/abc").status_code == 400
    assert client.get("/api/v1/reservas/64b7f0f0f0f0f0f0f0f0f0f0").status_code == 404


def test_conflicto_habitacion():
    assert crear().status_code == 201
    assert crear(huesped="Ana López").status_code == 409
    assert crear(habitacion="102").status_code == 201


def test_filtros():
    crear()
    crear(huesped="Ana López", habitacion="102", estado="confirmada", servicios=["spa"])
    assert len(client.get("/api/v1/reservas/").json()) == 2
    assert len(client.get("/api/v1/reservas/buscar?huesped=ana").json()) == 1
    assert len(client.get("/api/v1/reservas/estado/confirmada").json()) == 1
    assert len(client.get("/api/v1/reservas/habitacion/101").json()) == 1
    assert len(client.get("/api/v1/reservas/servicio/spa").json()) == 1
    assert len(client.get("/api/v1/reservas/fechas?fecha_entrada=2026-11-10").json()) == 2
    assert client.get("/api/v1/reservas/fechas").status_code == 422


def test_modificar_cancelar_eliminar():
    rid = crear().json()["_id"]
    r = client.put(f"/api/v1/reservas/{rid}", json={"cantidad_personas": 3})
    assert r.json()["cantidad_personas"] == 3
    assert client.patch(f"/api/v1/reservas/{rid}/cancelar").json()["estado"] == "cancelada"
    assert client.patch(f"/api/v1/reservas/{rid}/cancelar").status_code == 400
    assert client.delete(f"/api/v1/reservas/{rid}").status_code == 200
    assert client.delete(f"/api/v1/reservas/{rid}").status_code == 404
