"""
Bot Redes Sociales — Repuestos Madriz C.A.
Genera contenido para Instagram, WhatsApp, Facebook y TikTok usando Claude.
"""
import os
import json
import anthropic
from shared.db import database as db


def _claude():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


REDES = ["instagram", "whatsapp", "facebook", "tiktok"]


def generar_contenido(pieza: dict, red: str) -> dict:
    """Genera copy y hashtags para una pieza según la red social."""
    client = _claude()
    compat = ", ".join(pieza.get("compatibilidad") or [])

    estilos = {
        "instagram": "visual, emojis, máx 2200 caracteres, 15 hashtags relevantes",
        "whatsapp":  "directo, informal, máx 500 caracteres, precio destacado, sin hashtags",
        "facebook":  "informativo, amigable, máx 500 caracteres, 5 hashtags",
        "tiktok":    "energético, juvenil, máx 300 caracteres, 10 hashtags trending"
    }

    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=800,
        messages=[{"role": "user", "content": f"""
Eres community manager de una tienda de repuestos automotrices en Venezuela.
Genera contenido para {red.upper()}.
Estilo: {estilos.get(red, 'profesional')}

Datos del repuesto:
- Nombre: {pieza['nombre']}
- Marca: {pieza.get('marca','Genérico')}
- Compatible con: {compat or 'consultar'}
- Precio: ${pieza['precio_venta']:.2f}
- Tienda: Repuestos Madriz C.A.

Devuelve SOLO un JSON:
{{
  "contenido": "el texto del post",
  "hashtags": "#tag1 #tag2 ...",
  "llamada_accion": "texto del CTA"
}}
Solo el JSON."""}]
    )
    return json.loads(resp.content[0].text.strip())


def guardar_contenido(pieza_id: int, red: str, contenido: str, hashtags: str) -> int:
    return db.guardar_publicacion_red({
        "pieza_id":  pieza_id,
        "red":       red,
        "contenido": contenido,
        "hashtags":  hashtags,
        "estado":    "borrador"
    })


def listar_publicaciones(red: str = None) -> list[dict]:
    return db.publicaciones_red(red)
