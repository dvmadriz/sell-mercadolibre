# RepuestoBot — Especificaciones del Proyecto

## Uso
- Interno (operador único)
- Negocio de repuestos automotrices — Venezuela
- Mercado objetivo: Mercado Libre Venezuela (MLV)

---

## Bot 1 — MercadoLibre
- Publicación automática de piezas
- 3 fotos por pieza (diferentes ángulos)
- Ficha técnica generada por Claude Vision
- Búsqueda de compatibilidad por VIN / número de motor
- Gestión de stock y precios
- Verificación de pagos (Mercado Pago + foto comprobante)

## Bot 2 — Proveedores
- Búsqueda en Asia: Alibaba, Made-in-China, Global Sources
- Búsqueda en América: MercadoLibre, Amazon Business
- Comparación: precio unitario, envío, tiempo entrega, rating
- Precio sugerido de reventa con margen configurable
- Historial de compras por proveedor

## Bot 3 — Almacén
- Stock en tiempo real por pieza
- Registro de entradas y salidas
- Alertas de stock mínimo
- Búsqueda por código, VIN o número de motor
- Historial de movimientos

## Bot 4 — Redes Sociales
- Publicación automática: Instagram, WhatsApp, Facebook, TikTok
- Contenido generado por Claude (copy + hashtags)
- Video AI de la pieza (Runway ML)

---

## Módulo Vision (shared)
- Claude Vision lee foto + etiqueta
- Extrae: código, nombre, marca, tipo
- Decodifica VIN (17 dígitos) → marca, modelo, año, motor
- Decodifica número de motor → especificaciones exactas
- Mejora foto: Remove.bg + fondo profesional
- Genera ficha técnica estructurada

---

## Pendiente de definir
- [ ] Nombre final del proyecto
- [ ] Método de pago Venezuela (Zelle / Binance / Pago Móvil)
- [ ] Plataforma de interfaz (Telegram / Web / Script local)
- [ ] Fases de desarrollo y prioridades
