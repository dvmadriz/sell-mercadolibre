from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from bot_proveedores import proveedores as prov

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])


class BusquedaIn(BaseModel):
    pieza: str
    cantidad: int = 1
    margen_pct: float = 40


class ProveedorIn(BaseModel):
    nombre: str
    origen: Optional[str] = ""
    contacto: Optional[str] = ""
    notas: Optional[str] = ""


class PrecioIn(BaseModel):
    costo: float
    envio: float
    margen_pct: float = 40


@router.post("/buscar")
def buscar(datos: BusquedaIn):
    resultados = prov.buscar_proveedores_ia(datos.pieza, datos.cantidad)
    for r in resultados:
        r["precio_reventa_calculado"] = prov.precio_reventa_sugerido(
            r["precio_unitario_usd"], r["costo_envio_usd"], datos.margen_pct
        )
    return resultados


@router.get("/lista")
def listar():
    return prov.listar_proveedores()


@router.post("/registrar")
def registrar(datos: ProveedorIn):
    pid = prov.agregar_proveedor(datos.model_dump())
    return {"id": pid, "ok": True}


@router.post("/calcular-precio")
def calcular_precio(datos: PrecioIn):
    reventa = prov.precio_reventa_sugerido(datos.costo, datos.envio, datos.margen_pct)
    return {
        "costo_total":     round(datos.costo + datos.envio, 2),
        "precio_reventa":  reventa,
        "ganancia":        round(reventa - datos.costo - datos.envio, 2),
        "margen_pct":      datos.margen_pct,
    }
