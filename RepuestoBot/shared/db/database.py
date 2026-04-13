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
