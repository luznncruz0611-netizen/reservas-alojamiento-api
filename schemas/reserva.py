"""Esquemas Pydantic: validaciones de entrada y salida de las reservas."""
from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class EstadoReserva(str, Enum):
    pendiente = "pendiente"
    confirmada = "confirmada"
    cancelada = "cancelada"
    completada = "completada"


class Alojamiento(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Hotel Sol Andino"])
    ciudad: str = Field(..., min_length=2, max_length=100, examples=["Cochabamba"])


class ReservaBase(BaseModel):
    huesped: str = Field(..., min_length=2, max_length=100, examples=["Juan Pérez"])
    email: EmailStr = Field(..., examples=["juan@correo.com"])
    telefono: str = Field(..., pattern=r"^\+?[0-9\s\-]{7,15}$", examples=["+591 70012345"])
    habitacion: str = Field(..., min_length=1, max_length=20, examples=["101"])
    fecha_entrada: date = Field(..., examples=["2026-11-10"])
    fecha_salida: date = Field(..., examples=["2026-11-15"])
    cantidad_personas: int = Field(..., ge=1, le=20, examples=[2])
    estado: EstadoReserva = EstadoReserva.pendiente
    servicios: list[str] = Field(default_factory=list, examples=[["desayuno", "wifi"]])
    alojamiento: Alojamiento

    @field_validator("servicios")
    @classmethod
    def normalizar_servicios(cls, v: list[str]) -> list[str]:
        limpios = [s.strip().lower() for s in v if s and s.strip()]
        return list(dict.fromkeys(limpios))  # sin duplicados, conserva orden

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_salida <= self.fecha_entrada:
            raise ValueError("fecha_salida debe ser posterior a fecha_entrada")
        return self


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseModel):
    """Todos los campos son opcionales: solo se modifican los enviados."""

    huesped: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = None
    telefono: str | None = Field(None, pattern=r"^\+?[0-9\s\-]{7,15}$")
    habitacion: str | None = Field(None, min_length=1, max_length=20)
    fecha_entrada: date | None = None
    fecha_salida: date | None = None
    cantidad_personas: int | None = Field(None, ge=1, le=20)
    estado: EstadoReserva | None = None
    servicios: list[str] | None = None
    alojamiento: Alojamiento | None = None

    @field_validator("servicios")
    @classmethod
    def normalizar_servicios(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        limpios = [s.strip().lower() for s in v if s and s.strip()]
        return list(dict.fromkeys(limpios))


class ReservaOut(ReservaBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
