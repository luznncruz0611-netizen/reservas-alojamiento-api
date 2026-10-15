"""Punto de entrada: API de Sistema de Reservas de Alojamiento."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from api.v1.reservas import router as reservas_router

app = FastAPI(
    title="Sistema de Reservas de Alojamiento",
    description=(
        "API REST con **FastAPI** y **MongoDB** para administrar reservas: "
        "huéspedes, fechas, habitaciones, servicios y estado."
    ),
    version="1.0.0",
)

app.include_router(reservas_router, prefix="/api/v1")


@app.exception_handler(PyMongoError)
async def mongo_error_handler(request: Request, exc: PyMongoError):
    print("ERROR MONGO:", repr(exc))
    return JSONResponse(
        
        status_code=503,
        content={"detail": "Error de conexión con la base de datos. Intente más tarde."},
    )


@app.get("/", tags=["Inicio"])
def root():
    return {
        "mensaje": "API de Reservas de Alojamiento funcionando",
        "documentacion": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Inicio"])
def health():
    return {"status": "ok"}
