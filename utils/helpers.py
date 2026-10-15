"""Funciones auxiliares."""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from pymongo.collection import Collection


def to_object_id(reserva_id: str) -> ObjectId:
    """Convierte un string a ObjectId o lanza 400 si es inválido."""
    try:
        return ObjectId(reserva_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"ID inválido: '{reserva_id}'")


def serializar(doc: dict) -> dict:
    """Convierte el _id (ObjectId) a string para la respuesta JSON."""
    doc["_id"] = str(doc["_id"])
    return doc


def hay_conflicto(
    col: Collection,
    habitacion: str,
    entrada: str,
    salida: str,
    excluir_id: ObjectId | None = None,
) -> bool:
    """True si la habitación ya está reservada (no cancelada) en ese rango.

    Las fechas se guardan como texto ISO (YYYY-MM-DD), que se ordena correctamente.
    """
    query: dict = {
        "habitacion": habitacion,
        "estado": {"$ne": "cancelada"},
        "fecha_entrada": {"$lt": salida},
        "fecha_salida": {"$gt": entrada},
    }
    if excluir_id is not None:
        query["_id"] = {"$ne": excluir_id}
    return col.find_one(query) is not None
