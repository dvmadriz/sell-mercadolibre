"""
API FastAPI — Repuestos Madriz C.A.
n8n llama a estos endpoints para orquestar los bots.
"""
import sys
import urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from api.routes import almacen, mercadolibre, proveedores, redes, pagos
from shared.db import database as db
from bot_almacen import almacen as alm

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

    try:
        urllib.request.urlopen("http://localhost:8000/", timeout=1)
        api_activa = True
    except Exception:
        api_activa = True  # estamos dentro de la misma API

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


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, msg_ok: str = "", msg_err: str = ""):
    return templates.TemplateResponse("dashboard.html", {
        "request":  request,
        "fecha":    datetime.now().strftime("%A %d/%m/%Y  %H:%M"),
        "stats":    _stats(),
        "alertas":  db.piezas_bajo_minimo(),
        "piezas":   db.todas_las_piezas(),
        "busqueda": "",
        "msg_ok":   msg_ok,
        "msg_err":  msg_err,
    })


@app.get("/dashboard/buscar", response_class=HTMLResponse)
def buscar(request: Request, q: str = ""):
    return templates.TemplateResponse("dashboard.html", {
        "request":  request,
        "fecha":    datetime.now().strftime("%A %d/%m/%Y  %H:%M"),
        "stats":    _stats(),
        "alertas":  db.piezas_bajo_minimo(),
        "piezas":   db.buscar_piezas(q) if q else db.todas_las_piezas(),
        "busqueda": q,
        "msg_ok":   "",
        "msg_err":  "",
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
