"""
Bot Proveedores — Repuestos Madriz C.A.
Búsqueda de proveedores Asia/América con comparación de precios.
"""
import os
import json
import anthropic
from shared.db import database as db


def _claude():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def buscar_proveedores_ia(pieza: str, cantidad: int = 1) -> list[dict]:
    """
    Usa Claude para simular/analizar opciones de proveedores.
    En producción se puede complementar con scraping o APIs reales.
    """
    client = _claude()
    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"""
Eres un experto en compras de repuestos automotrices para revendedores venezolanos.
Pieza buscada: {pieza}
Cantidad: {cantidad} unidades

Genera una lista de 4 opciones realistas de proveedores (2 de Asia, 2 de América).
Devuelve SOLO un JSON con esta estructura:
[
  {{
    "proveedor": "nombre del proveedor/plataforma",
    "origen": "país",
    "precio_unitario_usd": 0.0,
    "costo_envio_usd": 0.0,
    "tiempo_entrega": "X días",
    "rating": "4.5/5",
    "precio_reventa_sugerido": 0.0,
    "margen_estimado_pct": 0,
    "notas": "observaciones"
  }}
]
Solo el JSON."""}]
    )
    resultados = json.loads(resp.content[0].text.strip())
    db.guardar_busqueda(pieza, "IA", resultados)
    return resultados


def precio_reventa_sugerido(costo: float, envio: float, margen_pct: float = 40) -> float:
    total_costo = costo + envio
    return round(total_costo * (1 + margen_pct / 100), 2)


def agregar_proveedor(datos: dict) -> int:
    return db.crear_proveedor(datos)


def listar_proveedores() -> list[dict]:
    return db.todos_los_proveedores()
