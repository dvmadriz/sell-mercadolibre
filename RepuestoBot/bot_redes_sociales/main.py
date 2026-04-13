"""
Bot Redes Sociales — Repuestos Madriz C.A.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from shared.db import database as db
from bot_redes_sociales import redes

console = Console()
REDES_COLORES = {
    "instagram": "magenta",
    "whatsapp":  "green",
    "facebook":  "blue",
    "tiktok":    "red"
}


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def pedir(texto: str, requerido: bool = True) -> str:
    while True:
        v = input(f"  {texto}: ").strip()
        if v or not requerido:
            return v
        console.print("  [red]Campo requerido.[/red]")


def menu_generar_contenido():
    limpiar()
    console.print(Panel("[bold cyan]Generar Contenido para Redes[/bold cyan]", box=box.ROUNDED))
    pieza_id = int(pedir("ID de la pieza"))
    pieza = db.obtener_pieza(pieza_id)
    if not pieza:
        console.print("  [red]Pieza no encontrada.[/red]")
        input("\n  Enter para continuar...")
        return

    console.print(f"  Pieza: [cyan]{pieza['nombre']}[/cyan]\n")
    console.print("  Redes disponibles:")
    for i, red in enumerate(redes.REDES, 1):
        color = REDES_COLORES.get(red, "white")
        console.print(f"  [bold]{i}.[/bold] [{color}]{red.capitalize()}[/{color}]")
    console.print("  [bold]5.[/bold] Todas")

    op = pedir("Elige red (1-5)")
    redes_elegidas = redes.REDES if op == "5" else [redes.REDES[int(op)-1]] if op in "1234" else []

    if not redes_elegidas:
        console.print("  [red]Opción inválida.[/red]")
        input("\n  Enter para continuar...")
        return

    for red in redes_elegidas:
        console.print(f"\n  [dim]Generando contenido para {red}...[/dim]")
        try:
            resultado = redes.generar_contenido(pieza, red)
            color = REDES_COLORES.get(red, "white")
            console.print(Panel(
                f"{resultado['contenido']}\n\n"
                f"[dim]{resultado['hashtags']}[/dim]\n\n"
                f"[bold]CTA:[/bold] {resultado.get('llamada_accion','')}",
                title=f"[{color}]{red.upper()}[/{color}]",
                box=box.ROUNDED
            ))
            guardar = input(f"  ¿Guardar este contenido para {red}? (s/n): ").strip().lower()
            if guardar == "s":
                pub_id = redes.guardar_contenido(
                    pieza_id, red,
                    resultado["contenido"],
                    resultado["hashtags"]
                )
                console.print(f"  [green]✓ Guardado (ID {pub_id}).[/green]")
        except Exception as e:
            console.print(f"  [red]Error en {red}: {e}[/red]")

    input("\n  Enter para continuar...")


def menu_ver_publicaciones():
    limpiar()
    console.print(Panel("[bold cyan]Publicaciones Guardadas[/bold cyan]", box=box.ROUNDED))
    console.print("  Filtrar por red: [1] Instagram  [2] WhatsApp  [3] Facebook  [4] TikTok  [5] Todas")
    op = input("  Opción: ").strip()
    filtro = None
    if op in "1234":
        filtro = redes.REDES[int(op)-1]

    pubs = redes.listar_publicaciones(filtro)
    if not pubs:
        console.print("  [dim]Sin publicaciones guardadas.[/dim]")
    else:
        t = Table(box=box.ROUNDED, show_lines=True)
        t.add_column("ID",      width=5)
        t.add_column("Red",     width=12)
        t.add_column("Contenido (preview)", width=50)
        t.add_column("Estado",  width=10)
        t.add_column("Fecha",   width=19)
        for p in pubs:
            color = REDES_COLORES.get(p["red"], "white")
            t.add_row(
                str(p["id"]),
                f"[{color}]{p['red']}[/{color}]",
                (p.get("contenido","")[:50] + "..."),
                p["estado"],
                p["fecha"]
            )
        console.print(t)
    input("\n  Enter para continuar...")


def main():
    db.init_db()
    while True:
        limpiar()
        console.print(Panel(
            "[bold white]REPUESTOS MADRIZ C.A.[/bold white]\n[dim]Bot Redes Sociales[/dim]",
            box=box.DOUBLE_EDGE, style="magenta"
        ))
        console.print("  [bold]1.[/bold] Generar contenido para una pieza")
        console.print("  [bold]2.[/bold] Ver publicaciones guardadas")
        console.print("  [bold]0.[/bold] Salir\n")

        op = input("  Opción: ").strip()
        if   op == "1": menu_generar_contenido()
        elif op == "2": menu_ver_publicaciones()
        elif op == "0":
            console.print("\n  [dim]Hasta luego.[/dim]\n")
            break


if __name__ == "__main__":
    main()
