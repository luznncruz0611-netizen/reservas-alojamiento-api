"""Conexión a MongoDB. Se usa UNA sola colección: `reservas`."""
from fastapi import HTTPException
from pymongo import MongoClient
from pymongo.collection import Collection

from core.config import settings

_client: MongoClient | None = None


def get_collection() -> Collection:
    """Devuelve la colección de reservas (cliente reutilizado entre invocaciones)."""
    global _client
    if not settings.mongodb_uri:
        raise HTTPException(
            status_code=500,
            detail="MONGODB_URI no está configurada en las variables de entorno.",
        )
    if _client is None:
        _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    return _client[settings.db_name][settings.collection_name]
