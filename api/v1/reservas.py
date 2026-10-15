"""Endpoints de la API de reservas."""
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.collection import Collection

from core.database import get_collection
from schemas.reserva import EstadoReserva, ReservaCreate, ReservaOut, ReservaUpdate
from utils.helpers import hay_conflicto, serializar, to_object_id

router = APIRouter(prefix="/reservas", tags=["Reservas"])

NO_ENCONTRADA = "Reserva no encontrada"


def _listar(col: Collection, filtro: dict, skip: int, limit: int) -> list[dict]:
    cursor = col.find(filtro).sort("fecha_entrada", 1).skip(skip).limit(limit)
    return [serializar(d) for d in cursor]


# ---------------------------------------------------------------- CREATE
@router.post(
    "/",
    response_model=ReservaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva reserva",
)
def crear_reserva(reserva: ReservaCreate, col: Collection = Depends(get_collection)):
    data = reserva.model_dump(mode="json")
    if data["estado"] != "cancelada" and hay_conflicto(
        col, data["habitacion"], data["fecha_entrada"], data["fecha_salida"]
    ):
        raise HTTPException(
            status_code=409,
            detail=f"La habitación {data['habitacion']} ya está reservada en esas fechas",
        )
    resultado = col.insert_one(data)
    data["_id"] = str(resultado.inserted_id)
    return data


# ------------------------------------------------------------------ READ
@router.get("/", response_model=list[ReservaOut], summary="Listar todas las reservas")
def listar_reservas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    col: Collection = Depends(get_collection),
):
    return _listar(col, {}, skip, limit)


@router.get(
    "/buscar",
    response_model=list[ReservaOut],
    summary="Buscar reservas por nombre del huésped",
)
def buscar_por_huesped(
    huesped: str = Query(..., min_length=1, description="Nombre (parcial, sin distinguir mayúsculas)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    col: Collection = Depends(get_collection),
):
    filtro = {"huesped": {"$regex": re.escape(huesped), "$options": "i"}}
    return _listar(col, filtro, skip, limit)


@router.get(
    "/estado/{estado}",
    response_model=list[ReservaOut],
    summary="Filtrar reservas por estado",
)
def filtrar_por_estado(
    estado: EstadoReserva,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    col: Collection = Depends(get_collection),
):
    return _listar(col, {"estado": estado.value}, skip, limit)


@router.get(
    "/habitacion/{habitacion}",
    response_model=list[ReservaOut],
    summary="Filtrar reservas por habitación",
)
def filtrar_por_habitacion(
    habitacion: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    col: Collection = Depends(get_collection),
):
    return _listar(col, {"habitacion": habitacion}, skip, limit)


@router.get(
    "/fechas",
    response_model=list[ReservaOut],
    summary="Filtrar reservas por fecha de entrada o salida",
    description=(
        "Use `fecha_entrada`/`fecha_salida` para coincidencia exacta, o los rangos "
        "`entrada_desde`/`entrada_hasta` y `salida_desde`/`salida_hasta`. "
        "Formato: YYYY-MM-DD. Debe enviarse al menos un parámetro."
    ),
)
def filtrar_por_fechas(
    fecha_entrada: date | None = None,
    fecha_salida: date | None = None,
    entrada_desde: date | None = None,
    entrada_hasta: date | None = None,
    salida_desde: date | None = None,
    salida_hasta: date | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    col: Collection = Depends(get_collection),
):
    filtro: dict = {}
    if fecha_entrada:
        filtro["fecha_entrada"] = fecha_entrada.isoformat()
    if fecha_salida:
        filtro["fecha_salida"] = fecha_salida.isoformat()

    rangos = {
        "fecha_entrada": (entrada_desde, entrada_hasta),
        "fecha_salida": (salida_desde, salida_hasta),
    }
    for campo, (desde, hasta) in rangos.items():
        if desde and hasta and desde > hasta:
            raise HTTPException(status_code=422, detail=f"Rango inválido para {campo}")
        rango: dict = {}
        if desde:
            rango["$gte"] = desde.isoformat()
        if hasta:
            rango["$lte"] = hasta.isoformat()
        if rango and campo not in filtro:
            filtro[campo] = rango

    if not filtro:
        raise HTTPException(status_code=422, detail="Debe enviar al menos un parámetro de fecha")
    return _listar(col, filtro, skip, limit)


@router.get(
    "/servicio/{servicio}",
    response_model=list[ReservaOut],
    summary="Consultar reservas que incluyan un servicio",
)
def filtrar_por_servicio(
    servicio: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    col: Collection = Depends(get_collection),
):
    return _listar(col, {"servicios": servicio.strip().lower()}, skip, limit)


@router.get(
    "/{reserva_id}",
    response_model=ReservaOut,
    summary="Consultar una reserva por su identificador",
)
def obtener_reserva(reserva_id: str, col: Collection = Depends(get_collection)):
    doc = col.find_one({"_id": to_object_id(reserva_id)})
    if not doc:
        raise HTTPException(status_code=404, detail=NO_ENCONTRADA)
    return serializar(doc)


# ---------------------------------------------------------------- UPDATE
@router.put(
    "/{reserva_id}",
    response_model=ReservaOut,
    summary="Modificar una reserva (campos parciales)",
)
def modificar_reserva(
    reserva_id: str,
    cambios: ReservaUpdate,
    col: Collection = Depends(get_collection),
):
    oid = to_object_id(reserva_id)
    actual = col.find_one({"_id": oid})
    if not actual:
        raise HTTPException(status_code=404, detail=NO_ENCONTRADA)

    nuevos = cambios.model_dump(mode="json", exclude_unset=True)
    if not nuevos:
        raise HTTPException(status_code=422, detail="No se envió ningún campo para modificar")

    final = {**actual, **nuevos}
    if final["fecha_salida"] <= final["fecha_entrada"]:
        raise HTTPException(
            status_code=422, detail="fecha_salida debe ser posterior a fecha_entrada"
        )
    if final["estado"] != "cancelada" and hay_conflicto(
        col, final["habitacion"], final["fecha_entrada"], final["fecha_salida"], excluir_id=oid
    ):
        raise HTTPException(
            status_code=409,
            detail=f"La habitación {final['habitacion']} ya está reservada en esas fechas",
        )

    col.update_one({"_id": oid}, {"$set": nuevos})
    return serializar(col.find_one({"_id": oid}))


@router.patch(
    "/{reserva_id}/cancelar",
    response_model=ReservaOut,
    summary="Cancelar una reserva (cambia el estado a 'cancelada')",
)
def cancelar_reserva(reserva_id: str, col: Collection = Depends(get_collection)):
    oid = to_object_id(reserva_id)
    doc = col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail=NO_ENCONTRADA)
    if doc["estado"] == "cancelada":
        raise HTTPException(status_code=400, detail="La reserva ya está cancelada")
    col.update_one({"_id": oid}, {"$set": {"estado": "cancelada"}})
    return serializar(col.find_one({"_id": oid}))


# ---------------------------------------------------------------- DELETE
@router.delete(
    "/{reserva_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar una reserva definitivamente",
)
def eliminar_reserva(reserva_id: str, col: Collection = Depends(get_collection)):
    resultado = col.delete_one({"_id": to_object_id(reserva_id)})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail=NO_ENCONTRADA)
    return {"mensaje": "Reserva eliminada correctamente", "id": reserva_id}
