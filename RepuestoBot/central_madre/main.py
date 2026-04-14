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
from datetime import datetime
import urllib.request

console = Console()


def pedir(texto: str, requerido: bool = True) -> str:
    while True:
        v = input(f"  {texto}: ").strip()
        if v or not requerido:
            return v
        console.print("  [red]Campo requerido.[/red]")


def pedir_numero(texto: str, tipo=float, requerido: bool = True):
    while True:
        raw = pedir(texto, requerido)
        if not raw and not requerido:
            return None
        try:
            return tipo(raw)
        except ValueError:
            console.print("  [red]Ingresa un número válido.[/red]")


def accion_buscar():
    from bot_almacen import almacen
    from rich.table import Table
    limpiar()
    console.print(Panel("[bold cyan]Búsqueda Rápida[/bold cyan]", box=box.ROUNDED))
    q = pedir("Código / nombre / marca / vehículo")
    piezas = almacen.buscar(q)
    if not piezas:
        console.print("  [dim]Sin resultados.[/dim]")
    else:
        t = Table(box=box.ROUNDED, show_lines=True)
        t.add_column("ID",      width=5,  style="dim")
        t.add_column("Código",  width=12, style="cyan")
        t.add_column("Nombre",  width=28)
        t.add_column("Marca",   width=12)
        t.add_column("Stock",   width=7,  justify="right")
        t.add_column("P.Venta", width=10, justify="right")
        t.add_column("Ubic.",   width=12, style="dim")
        for p in piezas:
            stock_style = "red bold" if p["stock"] <= p["stock_minimo"] else "white"
            t.add_row(
                str(p["id"]), p["codigo"], p["nombre"], p.get("marca",""),
                f"[{stock_style}]{p['stock']}[/{stock_style}]",
                f"${p['precio_venta']:.2f}", p.get("ubicacion","")
            )
        console.print(t)
    input("\n  Enter para continuar...")


def accion_entrada():
    from bot_almacen import almacen
    limpiar()
    console.print(Panel("[bold green]Entrada Rápida[/bold green]", box=box.ROUNDED))
    pieza_id = pedir_numero("ID de la pieza", tipo=int)
    pieza = db.obtener_pieza(pieza_id)
    if not pieza:
        console.print("  [red]Pieza no encontrada.[/red]")
        input("\n  Enter para continuar...")
        return
    console.print(f"  [cyan]{pieza['nombre']}[/cyan]  |  Stock actual: [yellow]{pieza['stock']}[/yellow]")
    cantidad  = pedir_numero("Cantidad", tipo=int)
    precio    = pedir_numero("Precio de costo unitario ($)")
    proveedor = pedir("Proveedor")
    alerta = almacen.registrar_entrada(pieza_id, cantidad, precio, proveedor)
    console.print(f"\n  [green]✓ Entrada registrada.[/green]")
    if alerta:
        console.print(f"  [bold yellow]⚠  {alerta}[/bold yellow]")
    input("\n  Enter para continuar...")


def accion_salida():
    from bot_almacen import almacen
    limpiar()
    console.print(Panel("[bold red]Salida Rápida[/bold red]", box=box.ROUNDED))
    pieza_id = pedir_numero("ID de la pieza", tipo=int)
    pieza = db.obtener_pieza(pieza_id)
    if not pieza:
        console.print("  [red]Pieza no encontrada.[/red]")
        input("\n  Enter para continuar...")
        return
    console.print(f"  [cyan]{pieza['nombre']}[/cyan]  |  Stock actual: [yellow]{pieza['stock']}[/yellow]")
    cantidad = pedir_numero("Cantidad", tipo=int)
    precio   = pedir_numero("Precio de venta unitario ($)")
    cliente  = pedir("Cliente")
    try:
        alerta = almacen.registrar_salida(pieza_id, cantidad, precio, cliente)
        console.print(f"\n  [green]✓ Salida registrada.[/green]")
        if alerta:
            console.print(f"  [bold yellow]⚠  {alerta}[/bold yellow]")
    except ValueError as e:
        console.print(f"\n  [red]⚠  {e}[/red]")
    input("\n  Enter para continuar...")


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def api_activa() -> bool:
    try:
        urllib.request.urlopen("http://localhost:8000/", timeout=1)
        return True
    except Exception:
        return False


def estado_sistema() -> list:
    """Retorna tarjetas de estado de cada módulo."""
    try:
        api     = api_activa()
        piezas  = db.todas_las_piezas()
        alertas = db.piezas_bajo_minimo()
        valor = db.valor_total_inventario()
        movs = db.movimientos_hoy()
        cobros = db.resumen_cobros_hoy()
        pubs_ml = db.todas_publicaciones_ml()
        pagos = db.pagos_pendientes()
        proveedores = db.todos_los_proveedores()
        redes_pubs = db.publicaciones_red()
    except Exception:
        return []

    publicadas = sum(1 for p in pubs_ml if p["estado"] == "publicado")

    tarjetas = [
        Panel(
            f"[white]Piezas:[/white]      [cyan]{len(piezas)}[/cyan]  [dim]({valor['unidades_total']} unid.)[/dim]\n"
            f"[white]Valor costo:[/white] [yellow]${valor['costo_total']:,.2f}[/yellow]\n"
            f"[white]Valor venta:[/white] [green]${valor['venta_total']:,.2f}[/green]\n"
            f"[white]Alertas:[/white]     [{'red bold' if alertas else 'green'}]{len(alertas)}[/{'red bold' if alertas else 'green'}]\n"
            f"[dim]── Hoy ──[/dim]\n"
            f"[white]Entradas:[/white]    [cyan]{movs['entradas']}[/cyan] unid.\n"
            f"[white]Salidas:[/white]     [magenta]{movs['salidas']}[/magenta] unid.  [green]${movs['vendido_hoy']:,.2f}[/green]",
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
        Panel(
            f"[white]API n8n:[/white]  [{'green' if api else 'red'}]{'● ACTIVA' if api else '● INACTIVA'}[/{'green' if api else 'red'}]\n"
            f"[dim]localhost:8000[/dim]\n\n"
            f"[dim]python3 run_api.py[/dim]" if not api else
            f"[white]API n8n:[/white]  [green]● ACTIVA[/green]\n"
            f"[dim]localhost:8000[/dim]\n"
            f"[dim]/docs disponible[/dim]",
            title="[bold]API / n8n[/bold]", box=box.ROUNDED,
            style="green" if api else "red"
        ),
        Panel(
            f"[dim]── Hoy ──[/dim]\n"
            f"[white]Confirmados:[/white] [green]{cobros['confirmados']}[/green]  [green]${cobros['confirmado_total']:,.2f}[/green]\n"
            f"[white]Pendientes:[/white]  [{'yellow bold' if cobros['pendientes'] else 'green'}]{cobros['pendientes']}[/{'yellow bold' if cobros['pendientes'] else 'green'}]  [dim]${cobros['pendiente_total']:,.2f}[/dim]\n"
            f"[dim]── Métodos ──[/dim]\n"
            f"[dim]Zelle · Binance · Pago Móvil[/dim]",
            title="[bold]Pagos VE[/bold]", box=box.ROUNDED, style="green"
        ),
    ]
    return tarjetas


def main():
    db.init_db()

    while True:
        limpiar()
        ahora = datetime.now().strftime("%A %d/%m/%Y   %H:%M")
        console.print(Panel(
            "[bold white]REPUESTOS MADRIZ C.A.[/bold white]\n"
            "[dim]Sistema RepuestoBot — Panel Principal[/dim]\n"
            f"[dim]{ahora}[/dim]",
            box=box.DOUBLE_EDGE, style="white"
        ))

        alertas = db.piezas_bajo_minimo()
        tarjetas = estado_sistema()
        if tarjetas:
            console.print(Columns(tarjetas))
            console.print()

        if alertas:
            for a in alertas:
                console.print(f"  [bold yellow]⚠  STOCK BAJO:[/bold yellow] [cyan]{a['nombre']}[/cyan] — {a['stock']} unid. (mín. {a['stock_minimo']})")
            console.print()

        console.print("  [dim]── Acciones rápidas ──[/dim]")
        console.print("  [bold]B.[/bold] Buscar pieza")
        console.print("  [bold]E.[/bold] Registrar entrada")
        console.print("  [bold]S.[/bold] Registrar salida")
        console.print("  [dim]── Módulos ──[/dim]")
        console.print("  [bold cyan]1.[/bold cyan] Bot Almacén        [dim]— inventario, entradas, salidas[/dim]")
        console.print("  [bold yellow]2.[/bold yellow] Bot MercadoLibre   [dim]— publicaciones, pagos, VIN[/dim]")
        console.print("  [bold blue]3.[/bold blue] Bot Proveedores    [dim]— búsqueda y comparación[/dim]")
        console.print("  [bold magenta]4.[/bold magenta] Bot Redes Sociales [dim]— contenido IA para redes[/dim]")
        console.print("  [bold green]5.[/bold green] Pagos Venezuela    [dim]— Zelle, Binance, Pago Móvil[/dim]")
        console.print("  [bold]0.[/bold] Salir\n")

        op = input("  Opción: ").strip().upper()

        if op == "B": accion_buscar()
        elif op == "E": accion_entrada()
        elif op == "S": accion_salida()
        elif op == "1":
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
        elif op == "5":
            from shared.pagos.main import main as pagos_main
            pagos_main()
        elif op == "0":
            console.print("\n  [dim]Hasta luego.[/dim]\n")
            break


if __name__ == "__main__":
    main()
