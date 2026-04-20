"""
Bot Proveedores — Repuestos Madriz C.A.
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
from shared.ui import limpiar, pedir, pedir_numero
from bot_proveedores import proveedores as prov

console = Console()


def menu_buscar_proveedor():
    limpiar()
    console.print(Panel("[bold cyan]Buscar Proveedores[/bold cyan]", box=box.ROUNDED))
    pieza = pedir("Nombre de la pieza a buscar")
    cantidad = pedir_numero("Cantidad a comprar", tipo=int)
    margen = pedir_numero("Margen de reventa % (ej: 40)", requerido=False)
    if margen is None:
        margen = 40.0

    console.print("  [dim]Buscando opciones con IA...[/dim]")
    try:
        resultados = prov.buscar_proveedores_ia(pieza, cantidad)

        t = Table(title=f"Opciones para: {pieza} x{cantidad}", box=box.ROUNDED, show_lines=True)
        t.add_column("Proveedor",   width=22)
        t.add_column("Origen",      width=12)
        t.add_column("P.Unit $",    width=9,  justify="right")
        t.add_column("Envío $",     width=8,  justify="right")
        t.add_column("Entrega",     width=12)
        t.add_column("Rating",      width=8)
        t.add_column("P.Reventa $", width=11, justify="right")
        t.add_column("Margen %",    width=9,  justify="right")
        t.add_column("Notas",       width=25)

        for r in resultados:
            reventa = prov.precio_reventa_sugerido(
                r["precio_unitario_usd"], r["costo_envio_usd"], margen
            )
            margen_real = round(
                (reventa - r["precio_unitario_usd"] - r["costo_envio_usd"])
                / max(r["precio_unitario_usd"] + r["costo_envio_usd"], 0.01) * 100
            )
            origen_color = "yellow" if r["origen"] in ("China","Asia") else "cyan"
            t.add_row(
                r["proveedor"],
                f"[{origen_color}]{r['origen']}[/{origen_color}]",
                f"${r['precio_unitario_usd']:.2f}",
                f"${r['costo_envio_usd']:.2f}",
                r["tiempo_entrega"],
                r["rating"],
                f"[green]${reventa:.2f}[/green]",
                f"{margen_real}%",
                r.get("notas","")[:25]
            )
        console.print(t)
    except Exception as e:
        console.print(f"\n  [red]Error: {e}[/red]")
    input("\n  Enter para continuar...")


def menu_agregar_proveedor():
    limpiar()
    console.print(Panel("[bold cyan]Registrar Proveedor[/bold cyan]", box=box.ROUNDED))
    datos = {
        "nombre":   pedir("Nombre del proveedor"),
        "origen":   pedir("País / origen", requerido=False),
        "contacto": pedir("Contacto (email/WhatsApp)", requerido=False),
        "notas":    pedir("Notas", requerido=False),
    }
    pid = prov.agregar_proveedor(datos)
    console.print(f"\n  [green]✓ Proveedor registrado con ID {pid}.[/green]")
    input("\n  Enter para continuar...")


def menu_listar_proveedores():
    limpiar()
    provs = prov.listar_proveedores()
    if not provs:
        console.print("  [dim]Sin proveedores registrados.[/dim]")
    else:
        t = Table(title="Proveedores registrados", box=box.ROUNDED)
        t.add_column("ID",       width=5)
        t.add_column("Nombre",   width=25)
        t.add_column("Origen",   width=15)
        t.add_column("Contacto", width=25)
        t.add_column("Notas",    width=25)
        for p in provs:
            t.add_row(str(p["id"]), p["nombre"], p.get("origen",""),
                      p.get("contacto",""), p.get("notas",""))
        console.print(t)
    input("\n  Enter para continuar...")


def menu_calcular_precio():
    limpiar()
    console.print(Panel("[bold cyan]Calcular Precio de Reventa[/bold cyan]", box=box.ROUNDED))
    costo  = pedir_numero("Precio de costo unitario ($)")
    envio  = pedir_numero("Costo de envío ($)")
    margen = pedir_numero("Margen deseado (%)")
    reventa = prov.precio_reventa_sugerido(costo, envio, margen)
    ganancia = reventa - costo - envio
    console.print(Panel(
        f"[bold]Costo total:[/bold]    ${costo + envio:.2f}\n"
        f"[bold]Precio reventa:[/bold] [green]${reventa:.2f}[/green]\n"
        f"[bold]Ganancia:[/bold]       [green]${ganancia:.2f}[/green]",
        title="Resultado", box=box.ROUNDED
    ))
    input("\n  Enter para continuar...")


def main():
    db.init_db()
    while True:
        limpiar()
        console.print(Panel(
            "[bold white]REPUESTOS MADRIZ C.A.[/bold white]\n[dim]Bot Proveedores[/dim]",
            box=box.DOUBLE_EDGE, style="blue"
        ))
        console.print("  [bold]1.[/bold] Buscar proveedores para una pieza")
        console.print("  [bold]2.[/bold] Registrar proveedor")
        console.print("  [bold]3.[/bold] Ver proveedores registrados")
        console.print("  [bold]4.[/bold] Calcular precio de reventa")
        console.print("  [bold]0.[/bold] Salir\n")

        op = input("  Opción: ").strip()
        if   op == "1": menu_buscar_proveedor()
        elif op == "2": menu_agregar_proveedor()
        elif op == "3": menu_listar_proveedores()
        elif op == "4": menu_calcular_precio()
        elif op == "0":
            console.print("\n  [dim]Hasta luego.[/dim]\n")
            break


if __name__ == "__main__":
    main()
