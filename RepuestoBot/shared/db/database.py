import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "data" / "repuestos_madriz.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS piezas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo        TEXT    UNIQUE NOT NULL,
            nombre        TEXT    NOT NULL,
            marca         TEXT,
            compatibilidad TEXT,
            stock         INTEGER NOT NULL DEFAULT 0,
            stock_minimo  INTEGER NOT NULL DEFAULT 1,
            precio_costo  REAL    NOT NULL DEFAULT 0,
            precio_venta  REAL    NOT NULL DEFAULT 0,
            ubicacion     TEXT,
            foto_path     TEXT,
            created_at    TEXT    NOT NULL,
            updated_at    TEXT    NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pieza_id     INTEGER NOT NULL,
            tipo         TEXT    NOT NULL CHECK(tipo IN ('entrada','salida')),
            cantidad     INTEGER NOT NULL,
            precio       REAL,
            contraparte  TEXT,
            fecha        TEXT    NOT NULL,
            notas        TEXT,
            FOREIGN KEY (pieza_id) REFERENCES piezas(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS publicaciones_ml (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pieza_id     INTEGER NOT NULL,
            ml_item_id   TEXT,
            titulo       TEXT,
            descripcion  TEXT,
            precio       REAL,
            estado       TEXT DEFAULT 'borrador',
            url          TEXT,
            fotos        TEXT,
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL,
            FOREIGN KEY (pieza_id) REFERENCES piezas(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL,
            origen       TEXT,
            contacto     TEXT,
            notas        TEXT,
            created_at   TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS busquedas_proveedor (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            termino      TEXT NOT NULL,
            plataforma   TEXT,
            resultados   TEXT,
            fecha        TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pieza_id     INTEGER,
            monto        REAL,
            metodo       TEXT,
            estado       TEXT DEFAULT 'pendiente',
            foto_path    TEXT,
            notas        TEXT,
            fecha        TEXT NOT NULL,
            FOREIGN KEY (pieza_id) REFERENCES piezas(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS publicaciones_redes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pieza_id     INTEGER,
            red          TEXT NOT NULL,
            contenido    TEXT,
            hashtags     TEXT,
            estado       TEXT DEFAULT 'borrador',
            fecha        TEXT NOT NULL,
            FOREIGN KEY (pieza_id) REFERENCES piezas(id)
        )
    """)

    conn.commit()
    conn.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── Piezas ────────────────────────────────────────────────────────────────────

def crear_pieza(datos: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    compat = json.dumps(datos.get("compatibilidad", []), ensure_ascii=False)
    cur.execute("""
        INSERT INTO piezas
            (codigo, nombre, marca, compatibilidad, stock, stock_minimo,
             precio_costo, precio_venta, ubicacion, foto_path, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        datos["codigo"], datos["nombre"], datos.get("marca", ""),
        compat, datos.get("stock", 0), datos.get("stock_minimo", 1),
        datos.get("precio_costo", 0), datos.get("precio_venta", 0),
        datos.get("ubicacion", ""), datos.get("foto_path", ""),
        now(), now()
    ))
    conn.commit()
    pieza_id = cur.lastrowid
    conn.close()
    return pieza_id


def actualizar_pieza(pieza_id: int, datos: dict):
    conn = get_connection()
    cur = conn.cursor()
    if "compatibilidad" in datos:
        datos["compatibilidad"] = json.dumps(datos["compatibilidad"], ensure_ascii=False)
    datos["updated_at"] = now()
    campos = ", ".join(f"{k}=?" for k in datos)
    cur.execute(f"UPDATE piezas SET {campos} WHERE id=?", (*datos.values(), pieza_id))
    conn.commit()
    conn.close()


def eliminar_pieza(pieza_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM piezas WHERE id=?", (pieza_id,))
    conn.commit()
    conn.close()


def obtener_pieza(pieza_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM piezas WHERE id=?", (pieza_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def buscar_piezas(termino: str) -> list[dict]:
    conn = get_connection()
    like = f"%{termino}%"
    rows = conn.execute("""
        SELECT * FROM piezas
        WHERE codigo LIKE ?
           OR nombre LIKE ?
           OR marca  LIKE ?
           OR compatibilidad LIKE ?
        ORDER BY nombre
    """, (like, like, like, like)).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def todas_las_piezas() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM piezas ORDER BY nombre").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def piezas_bajo_minimo() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM piezas WHERE stock <= stock_minimo ORDER BY nombre"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ── Movimientos ───────────────────────────────────────────────────────────────

def registrar_movimiento(pieza_id: int, tipo: str, cantidad: int,
                          precio: float, contraparte: str, notas: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO movimientos (pieza_id, tipo, cantidad, precio, contraparte, fecha, notas)
        VALUES (?,?,?,?,?,?,?)
    """, (pieza_id, tipo, cantidad, precio, contraparte, now(), notas))
    if tipo == "entrada":
        conn.execute("UPDATE piezas SET stock=stock+?, updated_at=? WHERE id=?",
                     (cantidad, now(), pieza_id))
    else:
        conn.execute("UPDATE piezas SET stock=MAX(0,stock-?), updated_at=? WHERE id=?",
                     (cantidad, now(), pieza_id))
    conn.commit()
    conn.close()


def movimientos_de_pieza(pieza_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM movimientos WHERE pieza_id=? ORDER BY fecha DESC",
        (pieza_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Publicaciones ML ──────────────────────────────────────────────────────────

def guardar_publicacion_ml(datos: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    fotos = json.dumps(datos.get("fotos", []), ensure_ascii=False)
    cur.execute("""
        INSERT INTO publicaciones_ml
            (pieza_id, ml_item_id, titulo, descripcion, precio, estado, url, fotos, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        datos["pieza_id"], datos.get("ml_item_id", ""),
        datos.get("titulo", ""), datos.get("descripcion", ""),
        datos.get("precio", 0), datos.get("estado", "borrador"),
        datos.get("url", ""), fotos, now(), now()
    ))
    conn.commit()
    pub_id = cur.lastrowid
    conn.close()
    return pub_id


def actualizar_publicacion_ml(pub_id: int, datos: dict):
    conn = get_connection()
    if "fotos" in datos:
        datos["fotos"] = json.dumps(datos["fotos"], ensure_ascii=False)
    datos["updated_at"] = now()
    campos = ", ".join(f"{k}=?" for k in datos)
    conn.execute(f"UPDATE publicaciones_ml SET {campos} WHERE id=?", (*datos.values(), pub_id))
    conn.commit()
    conn.close()


def publicaciones_ml_de_pieza(pieza_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM publicaciones_ml WHERE pieza_id=? ORDER BY created_at DESC",
        (pieza_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["fotos"] = json.loads(d["fotos"] or "[]")
        except Exception:
            d["fotos"] = []
        result.append(d)
    return result


def todas_publicaciones_ml() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT p.*, pz.nombre as pieza_nombre, pz.codigo as pieza_codigo "
        "FROM publicaciones_ml p JOIN piezas pz ON p.pieza_id=pz.id "
        "ORDER BY p.updated_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["fotos"] = json.loads(d["fotos"] or "[]")
        except Exception:
            d["fotos"] = []
        result.append(d)
    return result


# ── Proveedores ───────────────────────────────────────────────────────────────

def crear_proveedor(datos: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO proveedores (nombre, origen, contacto, notas, created_at)
        VALUES (?,?,?,?,?)
    """, (datos["nombre"], datos.get("origen",""), datos.get("contacto",""),
          datos.get("notas",""), now()))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def todos_los_proveedores() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM proveedores ORDER BY nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def guardar_busqueda(termino: str, plataforma: str, resultados: list):
    conn = get_connection()
    conn.execute("""
        INSERT INTO busquedas_proveedor (termino, plataforma, resultados, fecha)
        VALUES (?,?,?,?)
    """, (termino, plataforma, json.dumps(resultados, ensure_ascii=False), now()))
    conn.commit()
    conn.close()


# ── Pagos ─────────────────────────────────────────────────────────────────────

def registrar_pago(datos: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pagos (pieza_id, monto, metodo, estado, foto_path, notas, fecha)
        VALUES (?,?,?,?,?,?,?)
    """, (datos.get("pieza_id"), datos.get("monto", 0), datos.get("metodo",""),
          datos.get("estado","pendiente"), datos.get("foto_path",""),
          datos.get("notas",""), now()))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def actualizar_pago(pago_id: int, estado: str):
    conn = get_connection()
    conn.execute("UPDATE pagos SET estado=? WHERE id=?", (estado, pago_id))
    conn.commit()
    conn.close()


def pagos_pendientes() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM pagos WHERE estado='pendiente' ORDER BY fecha DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Redes Sociales ────────────────────────────────────────────────────────────

def guardar_publicacion_red(datos: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO publicaciones_redes (pieza_id, red, contenido, hashtags, estado, fecha)
        VALUES (?,?,?,?,?,?)
    """, (datos.get("pieza_id"), datos["red"], datos.get("contenido",""),
          datos.get("hashtags",""), datos.get("estado","borrador"), now()))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def publicaciones_red(red: str = None) -> list[dict]:
    conn = get_connection()
    if red:
        rows = conn.execute(
            "SELECT * FROM publicaciones_redes WHERE red=? ORDER BY fecha DESC", (red,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM publicaciones_redes ORDER BY fecha DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    try:
        d["compatibilidad"] = json.loads(d["compatibilidad"] or "[]")
    except Exception:
        d["compatibilidad"] = []
    return d
