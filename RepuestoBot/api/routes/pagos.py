from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from shared.pagos import pagos_venezuela as pv

router = APIRouter(prefix="/pagos", tags=["Pagos Venezuela"])


class CobroIn(BaseModel):
    pieza_id: Optional[int] = None
    monto: float
    metodo: str
    notas: Optional[str] = ""


class VerificarIn(BaseModel):
    pago_id: int
    ruta_foto: str
    metodo: str
    monto_esperado: float


class ConversionIn(BaseModel):
    monto_usd: float
    tasa: float


@router.post("/registrar")
def registrar_cobro(datos: CobroIn):
    if datos.metodo not in pv.METODOS.values():
        raise HTTPException(400, f"Método inválido. Opciones: {list(pv.METODOS.values())}")
    pago_id = pv.registrar_cobro(datos.model_dump())
    return {"id": pago_id, "ok": True}


@router.post("/verificar")
def verificar_comprobante(datos: VerificarIn):
    try:
        resultado = pv.verificar_comprobante(
            datos.ruta_foto, datos.metodo, datos.monto_esperado
        )
        if resultado["coincide_monto"] and resultado["estado_transaccion"] == "completado":
            pv.confirmar_cobro(datos.pago_id)
            resultado["accion"] = "confirmado"
        else:
            resultado["accion"] = "pendiente_revision"
        return resultado
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/confirmar/{pago_id}")
def confirmar(pago_id: int):
    pv.confirmar_cobro(pago_id)
    return {"ok": True}


@router.post("/rechazar/{pago_id}")
def rechazar(pago_id: int):
    pv.rechazar_cobro(pago_id)
    return {"ok": True}


@router.get("/pendientes")
def pendientes():
    return pv.cobros_pendientes()


@router.post("/convertir")
def convertir(datos: ConversionIn):
    ves = pv.tasa_usd_a_ves(datos.monto_usd, datos.tasa)
    return {"usd": datos.monto_usd, "tasa": datos.tasa, "ves": ves}
