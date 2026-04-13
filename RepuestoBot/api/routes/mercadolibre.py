from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from shared.db import database as db
from bot_mercadolibre import mercadolibre as ml

router = APIRouter(prefix="/mercadolibre", tags=["MercadoLibre"])


class PublicacionIn(BaseModel):
    pieza_id: int
    fotos: Optional[list[str]] = []
    titulo: Optional[str] = ""
    descripcion: Optional[str] = ""
    precio: float


class PagoFotoIn(BaseModel):
    ruta_foto: str
    monto_esperado: float
    pieza_id: Optional[int] = None


class VINIn(BaseModel):
    vin: str


@router.get("/publicaciones")
def listar_publicaciones():
    return db.todas_publicaciones_ml()


@router.post("/publicaciones")
def crear_publicacion(datos: PublicacionIn):
    pieza = db.obtener_pieza(datos.pieza_id)
    if not pieza:
        raise HTTPException(404, "Pieza no encontrada")

    titulo = datos.titulo
    descripcion = datos.descripcion

    if datos.fotos and not titulo:
        try:
            ficha = ml.generar_ficha(pieza, datos.fotos)
            titulo = ficha["titulo"]
            descripcion = ficha["descripcion"]
        except Exception:
            pass

    pub_id = db.guardar_publicacion_ml({
        "pieza_id":    datos.pieza_id,
        "titulo":      titulo or pieza["nombre"],
        "descripcion": descripcion or "",
        "precio":      datos.precio,
        "fotos":       datos.fotos,
        "estado":      "borrador"
    })
    return {"id": pub_id, "ok": True, "titulo": titulo}


@router.post("/verificar-pago")
def verificar_pago(datos: PagoFotoIn):
    try:
        resultado = ml.verificar_pago_foto(datos.ruta_foto, datos.monto_esperado)
        if resultado["coincide"] and datos.pieza_id:
            db.registrar_pago({
                "pieza_id":  datos.pieza_id,
                "monto":     resultado["monto_detectado"],
                "metodo":    resultado.get("metodo_pago", ""),
                "estado":    "confirmado",
                "foto_path": datos.ruta_foto,
                "notas":     resultado.get("referencia", ""),
            })
        return resultado
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/vin")
def decodificar_vin(datos: VINIn):
    resultado = ml.decodificar_vin(datos.vin)
    if not resultado.get("valido"):
        raise HTTPException(400, "VIN inválido o no reconocido")
    return resultado


@router.get("/pagos-pendientes")
def pagos_pendientes():
    return db.pagos_pendientes()
