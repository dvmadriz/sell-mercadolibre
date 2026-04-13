from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from shared.db import database as db
from bot_redes_sociales import redes

router = APIRouter(prefix="/redes", tags=["Redes Sociales"])


class ContenidoIn(BaseModel):
    pieza_id: int
    redes: list[str]


@router.post("/generar")
def generar_contenido(datos: ContenidoIn):
    pieza = db.obtener_pieza(datos.pieza_id)
    if not pieza:
        raise HTTPException(404, "Pieza no encontrada")

    resultados = []
    for red in datos.redes:
        if red not in redes.REDES:
            continue
        contenido = redes.generar_contenido(pieza, red)
        pub_id = redes.guardar_contenido(
            datos.pieza_id, red,
            contenido["contenido"], contenido["hashtags"]
        )
        resultados.append({"red": red, "id": pub_id, **contenido})
    return resultados


@router.get("/publicaciones")
def listar(red: Optional[str] = None):
    return redes.listar_publicaciones(red)
