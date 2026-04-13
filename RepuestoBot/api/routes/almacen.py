from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from shared.db import database as db
from bot_almacen import almacen

router = APIRouter(prefix="/almacen", tags=["Almacén"])


class PiezaIn(BaseModel):
    codigo: str
    nombre: str
    marca: Optional[str] = ""
    compatibilidad: Optional[list[str]] = []
    stock: int = 0
    stock_minimo: int = 1
    precio_costo: float = 0
    precio_venta: float = 0
    ubicacion: Optional[str] = ""
    foto_path: Optional[str] = ""


class MovimientoIn(BaseModel):
    pieza_id: int
    cantidad: int
    precio: float
    contraparte: str
    notas: Optional[str] = ""


@router.get("/piezas")
def listar_piezas():
    return almacen.listar_todo()


@router.get("/piezas/buscar")
def buscar_pieza(q: str):
    return almacen.buscar(q)


@router.get("/piezas/{pieza_id}")
def obtener_pieza(pieza_id: int):
    p = db.obtener_pieza(pieza_id)
    if not p:
        raise HTTPException(404, "Pieza no encontrada")
    return p


@router.post("/piezas")
def crear_pieza(datos: PiezaIn):
    pieza_id = almacen.agregar_pieza(datos.model_dump())
    return {"id": pieza_id, "ok": True}


@router.post("/entradas")
def registrar_entrada(mov: MovimientoIn):
    alerta = almacen.registrar_entrada(
        mov.pieza_id, mov.cantidad, mov.precio, mov.contraparte, mov.notas
    )
    return {"ok": True, "alerta": alerta}


@router.post("/salidas")
def registrar_salida(mov: MovimientoIn):
    try:
        alerta = almacen.registrar_salida(
            mov.pieza_id, mov.cantidad, mov.precio, mov.contraparte, mov.notas
        )
        return {"ok": True, "alerta": alerta}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/alertas")
def alertas_stock():
    return almacen.alertas_stock()


@router.get("/historial/{pieza_id}")
def historial(pieza_id: int):
    return almacen.historial(pieza_id)
