# RepuestoBot — Repuestos Madriz C.A.

Sistema de gestión para negocio de repuestos automotrices en Venezuela.

---

## Requisitos

- Python 3.11+
- Cuenta en [Anthropic](https://console.anthropic.com) para obtener la API Key

---

## Instalación

```bash
# 1. Instalar dependencias
pip3 install -r requirements.txt

# 2. Crear archivo de configuración
cp .env.example .env

# 3. Editar .env y agregar tu clave
#    ANTHROPIC_API_KEY=sk-ant-...
```

---

## Uso

```bash
python3 run.py
```

---

## Módulos

| Bot | Función |
|-----|---------|
| Almacén | Inventario, entradas/salidas, alertas de stock, búsqueda por foto |
| MercadoLibre | Publicaciones, ficha técnica IA, decodificador VIN, verificación de pagos |
| Proveedores | Búsqueda Asia/América, comparación de precios, cálculo de margen |
| Redes Sociales | Contenido IA para Instagram, WhatsApp, Facebook, TikTok |
| Pagos Venezuela | Zelle, Binance/USDT, Pago Móvil — verificación de comprobantes por foto |

---

## Variables de entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `ANTHROPIC_API_KEY` | Sí | API Key de Claude |
| `ML_ACCESS_TOKEN` | No | Token OAuth de MercadoLibre (para publicar directamente) |

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Lenguaje | Python 3.11+ |
| Base de datos | SQLite (local) |
| IA | Claude API (Vision + Text) |
| Marketplace | MercadoLibre Venezuela API |
| Interfaz | Script local (terminal) |

---

## Estado: verde Listo para pruebas
