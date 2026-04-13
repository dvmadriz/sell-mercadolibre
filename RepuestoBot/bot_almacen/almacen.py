"""
Lógica de negocio del Bot Almacén.
"""
from shared.db import database as db


def agregar_pieza(datos: dict) -> int:
    return db.crear_pieza(datos)


def editar_pieza(pieza_id: int, datos: dict):
    db.actualizar_pieza(pieza_id, datos)


def eliminar_pieza(pieza_id: int):
    db.eliminar_pieza(pieza_id)


def buscar(termino: str) -> list[dict]:
    return db.buscar_piezas(termino)


def listar_todo() -> list[dict]:
    return db.todas_las_piezas()


def registrar_entrada(pieza_id: int, cantidad: int, precio: float, proveedor: str, notas: str = ""):
    db.registrar_movimiento(pieza_id, "entrada", cantidad, precio, proveedor, notas)
    return _verificar_alerta(pieza_id)


def registrar_salida(pieza_id: int, cantidad: int, precio: float, cliente: str, notas: str = ""):
    pieza = db.obtener_pieza(pieza_id)
    if pieza and pieza["stock"] < cantidad:
        raise ValueError(f"Stock insuficiente. Disponible: {pieza['stock']}")
    db.registrar_movimiento(pieza_id, "salida", cantidad, precio, cliente, notas)
    return _verificar_alerta(pieza_id)


def historial(pieza_id: int) -> list[dict]:
    return db.movimientos_de_pieza(pieza_id)


def alertas_stock() -> list[dict]:
    return db.piezas_bajo_minimo()


def _verificar_alerta(pieza_id: int) -> str | None:
    pieza = db.obtener_pieza(pieza_id)
    if pieza and pieza["stock"] <= pieza["stock_minimo"]:
        return (f"ALERTA: '{pieza['nombre']}' tiene stock bajo "
                f"({pieza['stock']} unid. / mínimo {pieza['stock_minimo']})")
    return None
