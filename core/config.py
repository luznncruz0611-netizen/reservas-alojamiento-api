"""Configuración de la aplicación leída desde variables de entorno (.env)."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    db_name: str = os.getenv("DB_NAME", "reservas_db")
    collection_name: str = os.getenv("COLLECTION_NAME", "reservas")


settings = Settings()
