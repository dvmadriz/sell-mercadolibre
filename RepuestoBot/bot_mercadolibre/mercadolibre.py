"""
Bot MercadoLibre — Repuestos Madriz C.A.
Gestiona publicaciones, stock y verificación de pagos en MLV.
"""
import os
import json
import base64
from pathlib import Path
import anthropic
from shared.db import database as db


def _claude():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ── Ficha técnica con Claude Vision ──────────────────────────────────────────

def generar_ficha(pieza: dict, rutas_fotos: list[str]) -> dict:
    """Genera título, descripción y ficha técnica usando Claude Vision."""
    client = _claude()

    contenido = []
    for ruta in rutas_fotos[:3]:
        p = Path(ruta)
        if not p.exists():
            continue
        with open(p, "rb") as f:
            datos = base64.standard_b64encode(f.read()).decode()
        ext = p.suffix.lower()
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
        contenido.append({"type": "image", "source": {
            "type": "base64", "media_type": mime, "data": datos
        }})

    compat = ", ".join(pieza.get("compatibilidad") or [])
    contenido.append({"type": "text", "text": f"""
Eres un experto en repuestos automotrices venezolanos.
Datos del repuesto:
- Nombre: {pieza['nombre']}
- Marca: {pieza.get('marca', 'N/A')}
- Compatibilidad: {compat or 'Ver descripción'}
- Precio: ${pieza['precio_venta']:.2f}

Genera SOLO un JSON con esta estructura:
{{
  "titulo": "título para MercadoLibre (máx 60 caracteres)",
  "descripcion": "descripción completa y atractiva para compradores venezolanos",
  "condicion": "nuevo o usado",
  "categoria_sugerida": "categoría de MLV",
  "palabras_clave": ["kw1", "kw2", "kw3"]
}}
Solo el JSON, sin texto adicional.
"""})

    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": contenido}]
    )
    return json.loads(resp.content[0].text.strip())


def decodificar_vin(vin: str) -> dict:
    """Decodifica un VIN de 17 dígitos usando Claude."""
    client = _claude()
    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": f"""
Decodifica este VIN automotriz: {vin}
Devuelve SOLO un JSON:
{{
  "marca": "",
  "modelo": "",
  "anio": "",
  "motor": "",
  "pais_fabricacion": "",
  "tipo_vehiculo": "",
  "valido": true/false
}}
Solo el JSON."""}]
    )
    return json.loads(resp.content[0].text.strip())


def verificar_pago_foto(ruta_foto: str, monto_esperado: float) -> dict:
    """Analiza foto de comprobante de pago con Claude Vision."""
    client = _claude()
    p = Path(ruta_foto)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró: {ruta_foto}")
    with open(p, "rb") as f:
        datos = base64.standard_b64encode(f.read()).decode()
    ext = p.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png"}.get(ext, "image/jpeg")

    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": datos}},
            {"type": "text", "text": f"""
Analiza este comprobante de pago. Monto esperado: ${monto_esperado:.2f}
Devuelve SOLO un JSON:
{{
  "monto_detectado": 0.0,
  "coincide": true/false,
  "metodo_pago": "",
  "fecha_pago": "",
  "referencia": "",
  "confianza": "alta/media/baja",
  "observaciones": ""
}}
Solo el JSON."""}
        ]}]
    )
    return json.loads(resp.content[0].text.strip())


# ── Publicar en ML (requiere credenciales ML) ─────────────────────────────────

def publicar_en_ml(pub_id: int, access_token: str) -> dict:
    """
    Publica en MercadoLibre Venezuela.
    Requiere access_token OAuth de MLV.
    Retorna el item_id y URL si tiene éxito.
    """
    import urllib.request
    conn_db = db.get_connection()
    row = conn_db.execute(
        "SELECT p.*, pz.* FROM publicaciones_ml p JOIN piezas pz ON p.pieza_id=pz.id WHERE p.id=?",
        (pub_id,)
    ).fetchone()
    conn_db.close()
    if not row:
        raise ValueError("Publicación no encontrada")

    fotos = json.loads(row["fotos"] or "[]")
    payload = json.dumps({
        "title":        row["titulo"],
        "category_id":  "MLV1276",  # Repuestos Venezuela — ajustar según categoría real
        "price":        row["precio"],
        "currency_id":  "VES",
        "available_quantity": 1,
        "buying_mode":  "buy_it_now",
        "listing_type_id": "gold_special",
        "condition":    "used",
        "description":  {"plain_text": row["descripcion"]},
        "pictures":     [{"source": f} for f in fotos],
    }).encode()

    req = urllib.request.Request(
        "https://api.mercadolibre.com/items",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        resultado = json.loads(resp.read())

    db.actualizar_publicacion_ml(pub_id, {
        "ml_item_id": resultado.get("id", ""),
        "url":        resultado.get("permalink", ""),
        "estado":     "publicado"
    })
    return resultado


def pausar_publicacion_ml(ml_item_id: str, access_token: str):
    """Pausa una publicación activa en ML."""
    import urllib.request
    payload = json.dumps({"status": "paused"}).encode()
    req = urllib.request.Request(
        f"https://api.mercadolibre.com/items/{ml_item_id}",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {access_token}"},
        method="PUT"
    )
    with urllib.request.urlopen(req):
        pass
