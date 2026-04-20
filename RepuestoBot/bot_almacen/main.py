"""
Bot Almacén — Repuestos Madriz C.A.
Interfaz de línea de comandos (script local).
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# ── setup de paths ─────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from shared.db import database as db
from shared.ui import limpiar, pedir, pedir_numero, tabla_piezas
from bot_almacen import almacen

console = Console()


def mostrar_alerta(msg: str | None):
    if msg:
        console.print(f"\n  [bold yellow]⚠  {msg}[/bold yellow]")


def pedir_compatibilidad() -> list[str]:
    console.print("  Ingresa modelos compatibles (ej: Toyota Corolla 2018).")
    console.print("  Deja en blanco y presiona Enter para terminar.")
    items = []
    while True:
        val = input("    + ").strip()
        if not val:
            break
        items.append(val)
    return items


# ── menús ──────────────────────────────────────────────────────────────────

def menu_agregar():
    limpiar()
    console.print(Panel("[bold cyan]Agregar Pieza[/bold cyan]", box=box.ROUNDED))
    datos = {
        "codigo":       pedir("Código interno"),
        "nombre":       pedir("Nombre / descripción"),
        "marca":        pedir("Marca del repuesto", requerido=False),
        "stock":        pedir_numero("Stock inicial", tipo=int),
        "stock_minimo": pedir_numero("Stock mínimo para alerta", tipo=int),
        "precio_costo": pedir_numero("Precio de costo ($)"),
        "precio_venta": pedir_numero("Precio de venta ($)"),
        "ubicacion":    pedir("Ubicación (estante/caja)", requerido=False),
        "foto_path":    pedir("Ruta de la foto (opcional)", requerido=False),
    }
    datos["compatibilidad"] = pedir_compatibilidad()
    try:
        pieza_id = almacen.agregar_pieza(datos)
        console.print(f"\n  [green]✓ Pieza creada con ID {pieza_id}.[/green]")
    except Exception as e:
        console.print(f"\n  [red]Error: {e}[/red]")
    input("\n  Enter para continuar...")


def menu_buscar():
    limpiar()
    console.print(Panel("[bold cyan]Buscar Pieza[/bold cyan]", box=box.ROUNDED))
    termino = pedir("Buscar (código / nombre / marca / vehículo)")
    piezas = almacen.buscar(termino)
    tabla_piezas(piezas, f"Resultados para: {termino}")
    input("\n  Enter para continuar...")


def menu_buscar_por_foto():
    limpiar()
    console.print(Panel("[bold cyan]Buscar por Foto (Claude Vision)[/bold cyan]", box=box.ROUNDED))
    ruta = pedir("Ruta de la foto")
    console.print("  [dim]Analizando imagen...[/dim]")
    try:
        from shared.vision.vision import identificar_pieza
        resultado = identificar_pieza(ruta)
        console.print(Panel(
            f"[bold]Nombre:[/bold] {resultado.get('nombre')}\n"
            f"[bold]Marca:[/bold]  {resultado.get('marca')}\n"
            f"[bold]Tipo:[/bold]   {resultado.get('tipo')}\n"
            f"[bold]Código visible:[/bold] {resultado.get('codigo_visible') or 'N/A'}\n"
            f"[bold]Compatibilidad sugerida:[/bold] {', '.join(resultado.get('compatibilidad_sugerida', []))}\n"
            f"[bold]Notas:[/bold] {resultado.get('notas')}",
            title="Identificación", box=box.ROUNDED
        ))
        buscar = input("\n  ¿Buscar en inventario con este nombre? (s/n): ").strip().lower()
        if buscar == "s":
            piezas = almacen.buscar(resultado.get("nombre", ""))
            tabla_piezas(piezas, "Piezas similares en inventario")
    except Exception as e:
        console.print(f"\n  [red]Error: {e}[/red]")
    input("\n  Enter para continuar...")


def menu_entrada():
    limpiar()
    console.print(Panel("[bold green]Registrar Entrada[/bold green]", box=box.ROUNDED))
    pieza_id = pedir_numero("ID de la pieza", tipo=int)
    pieza = db.obtener_pieza(pieza_id)
    if not pieza:
        console.print("  [red]Pieza no encontrada.[/red]")
        input("\n  Enter para continuar...")
        return
    console.print(f"  Pieza: [cyan]{pieza['nombre']}[/cyan]  |  Stock actual: [yellow]{pieza['stock']}[/yellow]")
    cantidad   = pedir_numero("Cantidad que entró", tipo=int)
    precio     = pedir_numero("Precio de compra unitario ($)")
    proveedor  = pedir("Proveedor")
    notas      = pedir("Notas (opcional)", requerido=False)
    try:
        alerta = almacen.registrar_entrada(pieza_id, cantidad, precio, proveedor, notas)
        console.print(f"\n  [green]✓ Entrada registrada.[/green]")
        mostrar_alerta(alerta)
    except Exception as e:
        console.print(f"\n  [red]Error: {e}[/red]")
    input("\n  Enter para continuar...")


def menu_salida():
    limpiar()
    console.print(Panel("[bold red]Registrar Salida[/bold red]", box=box.ROUNDED))
    pieza_id = pedir_numero("ID de la pieza", tipo=int)
    pieza = db.obtener_pieza(pieza_id)
    if not pieza:
        console.print("  [red]Pieza no encontrada.[/red]")
        input("\n  Enter para continuar...")
        return
    console.print(f"  Pieza: [cyan]{pieza['nombre']}[/cyan]  |  Stock actual: [yellow]{pieza['stock']}[/yellow]")
    cantidad  = pedir_numero("Cantidad vendida", tipo=int)
    precio    = pedir_numero("Precio de venta unitario ($)")
    cliente   = pedir("Cliente")
    notas     = pedir("Notas (opcional)", requerido=False)
    try:
        alerta = almacen.registrar_salida(pieza_id, cantidad, precio, cliente, notas)
        console.print(f"\n  [green]✓ Salida registrada.[/green]")
        mostrar_alerta(alerta)
    except ValueError as e:
        console.print(f"\n  [red]⚠  {e}[/red]")
    except Exception as e:
        console.print(f"\n  [red]Error: {e}[/red]")
    input("\n  Enter para continuar...")


def menu_historial():
    limpiar()
    console.print(Panel("[bold cyan]Historial de Movimientos[/bold cyan]", box=box.ROUNDED))
    pieza_id = pedir_numero("ID de la pieza", tipo=int)
    pieza = db.obtener_pieza(pieza_id)
    if not pieza:
        console.print("  [red]Pieza no encontrada.[/red]")
        input("\n  Enter para continuar...")
        return
    movs = almacen.historial(pieza_id)
    if not movs:
        console.print("  [dim]Sin movimientos registrados.[/dim]")
    else:
        t = Table(title=f"Historial: {pieza['nombre']}", box=box.ROUNDED)
        t.add_column("Fecha",       width=19)
        t.add_column("Tipo",        width=8)
        t.add_column("Cant.",       justify="right", width=6)
        t.add_column("Precio",      justify="right", width=10)
        t.add_column("Contraparte", width=20)
        t.add_column("Notas",       width=25)
        for m in movs:
            color = "green" if m["tipo"] == "entrada" else "red"
            t.add_row(
                m["fecha"], f"[{color}]{m['tipo']}[/{color}]",
                str(m["cantidad"]), f"${m['precio']:.2f}",
                m.get("contraparte",""), m.get("notas","")
            )
        console.print(t)
    input("\n  Enter para continuar...")


def menu_alertas():
    limpiar()
    console.print(Panel("[bold yellow]Piezas con Stock Bajo[/bold yellow]", box=box.ROUNDED))
    piezas = almacen.alertas_stock()
    if not piezas:
        console.print("  [green]✓ Todo el inventario está por encima del mínimo.[/green]")
    else:
        tabla_piezas(piezas, "⚠  Stock bajo mínimo")
    input("\n  Enter para continuar...")


def menu_inventario():
    limpiar()
    piezas = almacen.listar_todo()
    tabla_piezas(piezas)
    input("\n  Enter para continuar...")


def menu_editar():
    limpiar()
    console.print(Panel("[bold cyan]Editar Pieza[/bold cyan]", box=box.ROUNDED))
    pieza_id = pedir_numero("ID de la pieza a editar", tipo=int)
    pieza = db.obtener_pieza(pieza_id)
    if not pieza:
        console.print("  [red]Pieza no encontrada.[/red]")
        input("\n  Enter para continuar...")
        return
    console.print(f"  Editando: [cyan]{pieza['nombre']}[/cyan]")
    console.print("  [dim](Deja en blanco para no cambiar el campo)[/dim]\n")
    campos = {}
    for campo, etiqueta in [
        ("nombre",        "Nombre"),
        ("marca",         "Marca"),
        ("stock_minimo",  "Stock mínimo"),
        ("precio_costo",  "Precio costo ($)"),
        ("precio_venta",  "Precio venta ($)"),
        ("ubicacion",     "Ubicación"),
        ("foto_path",     "Ruta foto"),
    ]:
        val = pedir(f"{etiqueta} [{pieza[campo]}]", requerido=False)
        if val:
            if campo in ("stock_minimo",):
                campos[campo] = int(val)
            elif campo in ("precio_costo", "precio_venta"):
                campos[campo] = float(val)
            else:
                campos[campo] = val
    if campos:
        almacen.editar_pieza(pieza_id, campos)
        console.print(f"\n  [green]✓ Pieza actualizada.[/green]")
    else:
        console.print("  [dim]Sin cambios.[/dim]")
    input("\n  Enter para continuar...")


# ── menú principal ─────────────────────────────────────────────────────────

def main():
    db.init_db()

    # Verificar alertas al arrancar
    alertas = almacen.alertas_stock()

    while True:
        limpiar()
        console.print(Panel(
            "[bold white]REPUESTOS MADRIZ C.A.[/bold white]\n"
            "[dim]Bot Almacén[/dim]",
            box=box.DOUBLE_EDGE, style="cyan"
        ))

        if alertas:
            console.print(f"  [bold yellow]⚠  {len(alertas)} pieza(s) con stock bajo mínimo.[/bold yellow]\n")

        console.print("  [bold]1.[/bold] Ver inventario completo")
        console.print("  [bold]2.[/bold] Buscar pieza")
        console.print("  [bold]3.[/bold] Buscar por foto  [dim](Claude Vision)[/dim]")
        console.print("  [bold]4.[/bold] Agregar pieza")
        console.print("  [bold]5.[/bold] Editar pieza")
        console.print("  [bold]6.[/bold] Registrar entrada")
        console.print("  [bold]7.[/bold] Registrar salida")
        console.print("  [bold]8.[/bold] Ver historial de movimientos")
        console.print("  [bold]9.[/bold] Ver alertas de stock")
        console.print("  [bold]0.[/bold] Salir\n")

        opcion = input("  Opción: ").strip()

        if   opcion == "1": menu_inventario()
        elif opcion == "2": menu_buscar()
        elif opcion == "3": menu_buscar_por_foto()
        elif opcion == "4": menu_agregar()
        elif opcion == "5": menu_editar()
        elif opcion == "6": menu_entrada()
        elif opcion == "7": menu_salida()
        elif opcion == "8": menu_historial()
        elif opcion == "9": menu_alertas()
        elif opcion == "0":
            console.print("\n  [dim]Hasta luego.[/dim]\n")
            break

        # Actualizar alertas después de cada acción
        alertas = almacen.alertas_stock()


if __name__ == "__main__":
    main()
