# RepuestoBot 🔧
**Sistema multi-bot para negocio de repuestos automotrices — Venezuela**

---

## Arquitectura

```
CENTRAL MADRE
│
├── bot_mercadolibre/     → Publicación, stock, pagos
├── bot_proveedores/      → Búsqueda Asia/América, precios, envíos
├── bot_almacen/          → Inventario, entradas, salidas, alertas
├── bot_redes_sociales/   → Instagram, WhatsApp, Facebook, TikTok
└── shared/
    ├── db/               → Base de datos central (Supabase)
    ├── utils/            → Funciones compartidas
    └── vision/           → Claude Vision, VIN decoder, foto enhancer
```

---

## Funciones Clave

- Claude Vision → lee foto + etiqueta → ficha técnica automática
- Decodificación VIN + número de motor → compatibilidad exacta
- Búsqueda de modelos/años compatibles por pieza
- Mejora de foto + fondo profesional (Remove.bg)
- Video AI de la pieza (Runway ML)
- Búsqueda de proveedores Asia/América con comparación de precios
- Verificación de pagos por foto de comprobante
- Publicación automática en Mercado Libre

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Lenguaje | Python 3.11+ |
| Framework | FastAPI |
| Base de datos | Supabase (PostgreSQL) |
| Hosting | Railway |
| IA | Claude API (Vision + Text) |
| Fotos | Remove.bg + Photoroom |
| Video | Runway ML |
| Marketplace | Mercado Libre API (MLV) |
| Pagos | Mercado Pago + verificación manual |

---

## Costo Estimado Mensual

| Servicio | Costo |
|----------|-------|
| Railway | ~$5/mes |
| Remove.bg | ~$9/mes |
| Runway ML | ~$15/mes |
| Claude API | Por uso |
| Supabase | Gratis (tier inicial) |
| **Total** | **~$30–50 USD/mes** |

---

## Estado: 🟡 En definición
