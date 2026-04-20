"""Shared terminal UI helpers for all bots."""
import os
from rich.console import Console
from rich.table import Table
from rich import box

_console = Console()


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def pedir(texto: str, requerido: bool = True) -> str:
    while True:
        v = input(f"  {texto}: ").strip()
        if v or not requerido:
            return v
        _console.print("  [red]Campo requerido.[/red]")


def pedir_numero(texto: str, tipo=float, requerido: bool = True):
    while True:
        raw = pedir(texto, requerido)
        if not raw and not requerido:
            return None
        try:
            return tipo(raw)
        except ValueError:
            _console.print("  [red]Ingresa un número válido.[/red]")


def tabla_piezas(piezas: list[dict], titulo: str = "Inventario"):
    if not piezas:
        _console.print("  [dim]No se encontraron piezas.[/dim]")
        return
    t = Table(title=titulo, box=box.ROUNDED, show_lines=True)
    t.add_column("ID",      style="dim",    width=5)
    t.add_column("Código",  style="cyan",   width=12)
    t.add_column("Nombre",  style="white",  width=28)
    t.add_column("Marca",   style="green",  width=12)
    t.add_column("Stock",   justify="right", width=7)
    t.add_column("Mín",     justify="right", width=5)
    t.add_column("P.Costo", justify="right", width=10)
    t.add_column("P.Venta", justify="right", width=10)
    t.add_column("Ubic.",   style="dim",    width=12)
    for p in piezas:
        stock_str   = str(p["stock"])
        stock_style = "red bold" if p["stock"] <= p["stock_minimo"] else "white"
        t.add_row(
            str(p["id"]), p["codigo"], p["nombre"], p.get("marca", ""),
            f"[{stock_style}]{stock_str}[/{stock_style}]",
            str(p["stock_minimo"]),
            f"${p['precio_costo']:.2f}", f"${p['precio_venta']:.2f}",
            p.get("ubicacion", "")
        )
    _console.print(t)
