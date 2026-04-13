import base64
import os
from pathlib import Path
import anthropic

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def identificar_pieza(ruta_foto: str) -> dict:
    """
    Recibe la ruta de una foto y devuelve un dict con:
    codigo_sugerido, nombre, marca, tipo, compatibilidad_sugerida, notas
    """
    ruta = Path(ruta_foto)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró la foto: {ruta_foto}")

    with open(ruta, "rb") as f:
        imagen_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    sufijo = ruta.suffix.lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                   ".png": "image/png", ".webp": "image/webp"}
    media_type = media_types.get(sufijo, "image/jpeg")

    prompt = """Eres un experto en repuestos automotrices.
Analiza esta foto de un repuesto y devuelve SOLO un JSON con esta estructura exacta:
{
  "nombre": "nombre técnico del repuesto",
  "marca": "marca si es visible, si no 'Genérico'",
  "tipo": "categoría (ej: filtro, correa, sensor, bomba, etc.)",
  "compatibilidad_sugerida": ["marcas/modelos posibles"],
  "codigo_visible": "código impreso en la pieza si es visible, si no ''",
  "notas": "observaciones relevantes"
}
Solo el JSON, sin texto adicional."""

    client = _get_client()
    mensaje = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": imagen_b64
                }},
                {"type": "text", "text": prompt}
            ]
        }]
    )

    import json
    texto = mensaje.content[0].text.strip()
    return json.loads(texto)
