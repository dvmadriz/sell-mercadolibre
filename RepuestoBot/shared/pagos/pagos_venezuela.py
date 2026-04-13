"""
Módulo de pagos Venezuela — Repuestos Madriz C.A.
Soporta: Zelle, Binance/USDT, Pago Móvil.
Verificación manual + Claude Vision para comprobantes.
"""
import os
import json
import base64
from pathlib import Path
from datetime import datetime
import anthropic
from shared.db import database as db


METODOS = {
    "1": "zelle",
    "2": "binance",
    "3": "pago_movil",
}

METODO_INFO = {
    "zelle": {
        "nombre":   "Zelle",
        "moneda":   "USD",
        "datos":    "Email o número de teléfono Zelle del destinatario",
        "tips":     "El comprobante debe mostrar monto, fecha y confirmación."
    },
    "binance": {
        "nombre":   "Binance / USDT",
        "moneda":   "USDT",
        "datos":    "Dirección de wallet o UID de Binance Pay",
        "tips":     "Pide captura del historial de transferencia Binance."
    },
    "pago_movil": {
        "nombre":   "Pago Móvil",
        "moneda":   "VES",
        "datos":    "Banco, RIF/CI y número de teléfono del destinatario",
        "tips":     "El comprobante debe tener número de referencia y fecha."
    },
}


def _claude():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def verificar_comprobante(ruta_foto: str, metodo: str, monto_esperado: float) -> dict:
    """
    Analiza foto del comprobante según el método de pago.
    Retorna dict con resultado del análisis.
    """
    p = Path(ruta_foto)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró: {ruta_foto}")

    with open(p, "rb") as f:
        datos_b64 = base64.standard_b64encode(f.read()).decode()
    ext = p.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")

    info = METODO_INFO.get(metodo, {})
    client = _claude()

    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {
                "type": "base64", "media_type": mime, "data": datos_b64
            }},
            {"type": "text", "text": f"""
Analiza este comprobante de pago.
Método: {info.get('nombre', metodo)}
Moneda esperada: {info.get('moneda','USD')}
Monto esperado: {monto_esperado:.2f}

Devuelve SOLO un JSON:
{{
  "monto_detectado": 0.0,
  "moneda": "",
  "coincide_monto": true/false,
  "fecha_pago": "",
  "referencia": "",
  "remitente": "",
  "destinatario": "",
  "estado_transaccion": "completado/pendiente/rechazado/no_visible",
  "confianza": "alta/media/baja",
  "observaciones": ""
}}
Solo el JSON."""}
        ]}]
    )
    return json.loads(resp.content[0].text.strip())


def registrar_cobro(datos: dict) -> int:
    """Guarda el cobro en la base de datos."""
    return db.registrar_pago({
        "pieza_id":  datos.get("pieza_id"),
        "monto":     datos["monto"],
        "metodo":    datos["metodo"],
        "estado":    datos.get("estado", "pendiente"),
        "foto_path": datos.get("foto_path", ""),
        "notas":     datos.get("notas", ""),
    })


def confirmar_cobro(pago_id: int):
    db.actualizar_pago(pago_id, "confirmado")


def rechazar_cobro(pago_id: int):
    db.actualizar_pago(pago_id, "rechazado")


def cobros_pendientes() -> list[dict]:
    return db.pagos_pendientes()


def tasa_usd_a_ves(monto_usd: float, tasa: float) -> float:
    """Convierte USD a VES con la tasa del día."""
    return round(monto_usd * tasa, 2)
