"""
Central Madre — Repuestos Madriz C.A.
Panel principal que conecta todos los bots.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from shared.db import database as db

console = Console()


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def estado_sistema() -> list:
    """Retorna tarjetas de estado de cada módulo."""
    try:
        piezas = db.todas_las_piezas()
        alertas = db.piezas_bajo_minimo()
        pubs_ml = db.todas_publicaciones_ml()
        pagos = db.pagos_pendientes()
        proveedores = db.todos_los_proveedores()
        redes_pubs = db.publicaciones_red()
    except Exception:
        return []

    publicadas = sum(1 for p in pubs_ml if p["estado"] == "publicado")

    tarjetas = [
        Panel(
            f"[white]Piezas en stock:[/white] [cyan]{len(piezas)}[/cyan]\n"
            f"[white]Alertas stock:[/white]   [{'red' if alertas else 'green'}]{len(alertas)}[/{'red' if alertas else 'green'}]",
            title="[bold]Almacén[/bold]", box=box.ROUNDED, style="cyan"
        ),
        Panel(
            f"[white]Publicaciones:[/white]  [cyan]{len(pubs_ml)}[/cyan]\n"
            f"[white]Publicadas ML:[/white]  [green]{publicadas}[/green]\n"
            f"[white]Pagos pendientes:[/white][{'yellow' if pagos else 'green'}]{len(pagos)}[/{'yellow' if pagos else 'green'}]",
            title="[bold]MercadoLibre[/bold]", box=box.ROUNDED, style="yellow"
        ),
        Panel(
            f"[white]Proveedores:[/white]  [cyan]{len(proveedores)}[/cyan]",
            title="[bold]Proveedores[/bold]", box=box.ROUNDED, style="blue"
        ),
        Panel(
            f"[white]Contenido guardado:[/white] [cyan]{len(redes_pubs)}[/cyan]",
            title="[bold]Redes Sociales[/bold]", box=box.ROUNDED, style="magenta"
        ),
    ]
    return tarjetas


def main():
    db.init_db()

    while True:
        limpiar()
        console.print(Panel(
            "[bold white]REPUESTOS MADRIZ C.A.[/bold white]\n"
            "[dim]Sistema RepuestoBot — Panel Principal[/dim]",
            box=box.DOUBLE_EDGE, style="white"
        ))

        tarjetas = estado_sistema()
        if tarjetas:
            console.print(Columns(tarjetas))
            console.print()

        console.print("  [bold cyan]1.[/bold cyan] Bot Almacén        [dim]— inventario, entradas, salidas[/dim]")
        console.print("  [bold yellow]2.[/bold yellow] Bot MercadoLibre   [dim]— publicaciones, pagos, VIN[/dim]")
        console.print("  [bold blue]3.[/bold blue] Bot Proveedores    [dim]— búsqueda y comparación[/dim]")
        console.print("  [bold magenta]4.[/bold magenta] Bot Redes Sociales [dim]— contenido IA para redes[/dim]")
        console.print("  [bold]0.[/bold] Salir\n")

        op = input("  Opción: ").strip()

        if op == "1":
            from bot_almacen.main import main as almacen_main
            almacen_main()
        elif op == "2":
            from bot_mercadolibre.main import main as ml_main
            ml_main()
        elif op == "3":
            from bot_proveedores.main import main as prov_main
            prov_main()
        elif op == "4":
            from bot_redes_sociales.main import main as redes_main
            redes_main()
        elif op == "0":
            console.print("\n  [dim]Hasta luego.[/dim]\n")
            break


if __name__ == "__main__":
    main()
