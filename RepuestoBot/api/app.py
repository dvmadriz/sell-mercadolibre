"""
API FastAPI — Repuestos Madriz C.A.
n8n llama a estos endpoints para orquestar los bots.
"""
import os
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from api.routes import almacen, mercadolibre, proveedores, redes, pagos
from shared.db import database as db
from bot_almacen import almacen as alm
from bot_mercadolibre import mercadolibre as ml
import anthropic
import json

app = FastAPI(
    title="RepuestoBot API",
    description="Repuestos Madriz C.A. — Backend para n8n",
    version="1.0.0"
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

db.init_db()

app.include_router(almacen.router)
app.include_router(mercadolibre.router)
app.include_router(proveedores.router)
app.include_router(redes.router)
app.include_router(pagos.router)


def _stats():
    piezas      = db.todas_las_piezas()
    alertas     = db.piezas_bajo_minimo()
    valor       = db.valor_total_inventario()
    movs        = db.movimientos_hoy()
    cobros      = db.resumen_cobros_hoy()
    pubs_ml     = db.todas_publicaciones_ml()
    pagos_pend  = db.pagos_pendientes()
    provs       = db.todos_los_proveedores()
    redes_pubs  = db.publicaciones_red()
    publicadas  = sum(1 for p in pubs_ml if p["estado"] == "publicado")

    api_activa = True  # siempre True: esta función corre dentro de la API

    return {
        "piezas":             len(piezas),
        "unidades":           valor["unidades_total"],
        "costo_total":        valor["costo_total"],
        "venta_total":        valor["venta_total"],
        "alertas":            len(alertas),
        "entradas_hoy":       movs["entradas"],
        "salidas_hoy":        movs["salidas"],
        "vendido_hoy":        movs["vendido_hoy"],
        "publicaciones":      len(pubs_ml),
        "publicadas":         publicadas,
        "pagos_pendientes":   len(pagos_pend),
        "proveedores":        len(provs),
        "redes_pubs":         len(redes_pubs),
        "cobros_confirmados": cobros["confirmados"],
        "cobros_pendientes":  cobros["pendientes"],
        "cobrado_hoy":        cobros["confirmado_total"],
        "pendiente_hoy":      cobros["pendiente_total"],
        "api_activa":         api_activa,
    }


@app.get("/ficha", response_class=HTMLResponse)
def ficha_page(request: Request):
    return templates.TemplateResponse("ficha.html", {"request": request})


class FichaIn(BaseModel):
    codigo:       Optional[str] = ""
    vin:          Optional[str] = ""
    motor:        Optional[str] = ""
    image_base64: Optional[str] = None
    sources:      Optional[list[str]] = []


@app.post("/ficha/generar")
def ficha_generar(datos: FichaIn):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""Eres un experto en repuestos automotrices. Datos: código={datos.codigo or '-'}, VIN={datos.vin or '-'}, motor={datos.motor or '-'}.
Genera ficha técnica completa en JSON sin markdown:
{{"codigo":"","nombre":"","marca_fabricante":"","numero_oem":"","tipo":"","descripcion":"",
"especificaciones":{{"material":"","peso_kg":"","dimensiones":"","voltaje":"","presion_bar":""}},
"compatibilidad":["Toyota Corolla 2008-2019"],
"precios":{{"rockauto_usd":0,"toyota_oem_usd":0,"chevrolet_usd":0,"ford_usd":0}},
"precio_minimo_usd":0,"precio_sugerido_venta_usd":0,"margen_porcentaje":0,
"anos_aplicacion":"","notas_tecnicas":""}}
Solo el JSON."""

    if datos.image_base64:
        content = [
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/jpeg", "data": datos.image_base64
            }},
            {"type": "text", "text": prompt}
        ]
    else:
        content = prompt

    resp = client.messages.create(
        model="claude-opus-4-7", max_tokens=1200,
        messages=[{"role": "user", "content": content}]
    )
    texto = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return JSONResponse(content=json.loads(texto))


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, msg_ok: str = "", msg_err: str = ""):
    return templates.TemplateResponse("dashboard.html", {
        "request":  request,
        "fecha":    datetime.now().strftime("%A %d/%m/%Y  %H:%M"),
        "stats":    _stats(),
        "alertas":  db.piezas_bajo_minimo(),
        "piezas":   db.todas_las_piezas(),
        "busqueda":      "",
        "msg_ok":        msg_ok,
        "msg_err":       msg_err,
        "vin_resultado": None,
        "piezas_vin":    [],
    })


@app.get("/dashboard/buscar", response_class=HTMLResponse)
def buscar(request: Request, q: str = ""):
    return templates.TemplateResponse("dashboard.html", {
        "request":  request,
        "fecha":    datetime.now().strftime("%A %d/%m/%Y  %H:%M"),
        "stats":    _stats(),
        "alertas":  db.piezas_bajo_minimo(),
        "piezas":   db.buscar_piezas(q) if q else db.todas_las_piezas(),
        "busqueda":      q,
        "msg_ok":        "",
        "msg_err":       "",
        "vin_resultado": None,
        "piezas_vin":    [],
    })


@app.post("/dashboard/entrada")
def entrada(
    pieza_id: int  = Form(...),
    cantidad: int  = Form(...),
    precio:   float = Form(...),
    proveedor: str = Form(...),
):
    try:
        alm.registrar_entrada(pieza_id, cantidad, precio, proveedor)
        return RedirectResponse("/?msg_ok=Entrada+registrada", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/?msg_err={str(e)}", status_code=303)


@app.get("/dashboard/vin", response_class=HTMLResponse)
def vin_decoder(request: Request, vin: str = ""):
    vin_resultado = None
    piezas_vin = []
    if vin:
        try:
            vin_resultado = ml.decodificar_vin(vin)
            if vin_resultado.get("valido"):
                termino = f"{vin_resultado['marca']} {vin_resultado['modelo']} {vin_resultado['anio']}"
                piezas_vin = db.buscar_piezas(termino)
        except Exception as e:
            vin_resultado = {"valido": False, "error": str(e)}
    return templates.TemplateResponse("dashboard.html", {
        "request":      request,
        "fecha":        datetime.now().strftime("%A %d/%m/%Y  %H:%M"),
        "stats":        _stats(),
        "alertas":      db.piezas_bajo_minimo(),
        "piezas":       db.todas_las_piezas(),
        "busqueda":     "",
        "msg_ok":       "",
        "msg_err":      "",
        "vin_resultado": vin_resultado,
        "piezas_vin":   piezas_vin,
    })


@app.post("/dashboard/salida")
def salida(
    pieza_id: int  = Form(...),
    cantidad: int  = Form(...),
    precio:   float = Form(...),
    cliente:  str  = Form(...),
):
    try:
        alm.registrar_salida(pieza_id, cantidad, precio, cliente)
        return RedirectResponse("/?msg_ok=Salida+registrada", status_code=303)
    except ValueError as e:
        return RedirectResponse(f"/?msg_err={str(e)}", status_code=303)
