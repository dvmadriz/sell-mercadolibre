"""
API FastAPI — Repuestos Madriz C.A.
n8n llama a estos endpoints para orquestar los bots.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from api.routes import almacen, mercadolibre, proveedores, redes, pagos
from shared.db import database as db

app = FastAPI(
    title="RepuestoBot API",
    description="Repuestos Madriz C.A. — Backend para n8n",
    version="1.0.0"
)

db.init_db()

app.include_router(almacen.router)
app.include_router(mercadolibre.router)
app.include_router(proveedores.router)
app.include_router(redes.router)
app.include_router(pagos.router)


@app.get("/")
def health():
    return {"status": "ok", "sistema": "RepuestoBot — Repuestos Madriz C.A."}
